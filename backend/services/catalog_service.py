"""
Product Catalog Service — WhatsApp catalog browsing, image handling, product recommendations.
Works with Product model and provides catalog formatting for WhatsApp.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc, func
from loguru import logger

from models import Product


class CatalogService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_products(self, business_id: str, query: str, limit: int = 10) -> list:
        """Search products by name, category, brand, tags, or description."""
        try:
            query_lower = f"%{query.lower()}%"
            result = await self.db.execute(
                select(Product).where(
                    Product.business_id == business_id,
                    Product.is_active == True,
                    or_(
                        Product.name.ilike(query_lower),
                        Product.category.ilike(query_lower),
                        Product.brand.ilike(query_lower),
                        Product.description.ilike(query_lower),
                    ),
                ).order_by(desc(Product.stock_quantity)).limit(limit)
            )
            products = result.scalars().all()
            return [self._product_to_dict(p) for p in products]
        except Exception as e:
            logger.error("Product search error: {}", e)
            return []

    async def get_catalog(self, business_id: str, category: str = None,
                          page: int = 1, per_page: int = 20) -> dict:
        """Get paginated product catalog."""
        try:
            query = select(Product).where(
                Product.business_id == business_id,
                Product.is_active == True,
            )
            if category:
                query = query.where(Product.category == category)

            # Count
            count_result = await self.db.execute(
                select(func.count(Product.id)).where(
                    Product.business_id == business_id,
                    Product.is_active == True,
                )
            )
            total = count_result.scalar() or 0

            # Paginate
            offset = (page - 1) * per_page
            result = await self.db.execute(
                query.order_by(Product.name).offset(offset).limit(per_page)
            )
            products = result.scalars().all()

            return {
                "products": [self._product_to_dict(p) for p in products],
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page,
            }
        except Exception as e:
            logger.error("Catalog fetch error: {}", e)
            return {"products": [], "total": 0, "page": 1, "per_page": per_page, "total_pages": 0}

    async def get_categories(self, business_id: str) -> list:
        """Get all product categories."""
        try:
            result = await self.db.execute(
                select(Product.category).where(
                    Product.business_id == business_id,
                    Product.is_active == True,
                    Product.category.isnot(None),
                ).distinct()
            )
            return [row[0] for row in result.all() if row[0]]
        except Exception:
            return []

    async def get_product(self, product_id: str) -> Optional[dict]:
        """Get single product by ID."""
        try:
            result = await self.db.execute(
                select(Product).where(Product.id == product_id)
            )
            product = result.scalar_one_or_none()
            return self._product_to_dict(product) if product else None
        except Exception:
            return None

    async def get_recommendations(self, business_id: str, product_id: str = None,
                                   category: str = None, limit: int = 5) -> list:
        """Get product recommendations based on category or purchase history."""
        try:
            query = select(Product).where(
                Product.business_id == business_id,
                Product.is_active == True,
                Product.stock_quantity > 0,
            )
            if category:
                query = query.where(Product.category == category)
            if product_id:
                # Exclude current product
                query = query.where(Product.id != product_id)

            result = await self.db.execute(
                query.order_by(desc(Product.stock_quantity)).limit(limit)
            )
            return [self._product_to_dict(p) for p in result.scalars().all()]
        except Exception:
            return []

    async def format_catalog_for_whatsapp(self, business_id: str, category: str = None) -> str:
        """Format catalog as WhatsApp-friendly message."""
        catalog = await self.get_catalog(business_id, category, per_page=10)
        products = catalog["products"]

        if not products:
            return "Maaf kijiye, abhi koi products available nahi hain! 😔\n\nKuch aur pooch sakte ho — pricing, service, ya support!"

        lines = ["*Hamare Products:* 🛍️\n"]
        for i, p in enumerate(products, 1):
            stock_icon = "✅" if p["stock"] > 0 else "❌"
            lines.append(f"{i}. {stock_icon} *{p['name']}* — ₹{p['price']}/{p.get('unit', 'pc')}")
            if p.get("category"):
                lines.append(f"   📂 {p['category']}")
            if p["stock"] > 0:
                lines.append(f"   📦 {p['stock']} available")
            lines.append("")

        total = catalog["total"]
        if total > 10:
            lines.append(f"... aur {total - 10} products hain! Category bolo ya search karo.")

        lines.append("\nKya lena hai? Number ya naam batao! 🛒")
        return "\n".join(lines)

    async def format_product_detail(self, product_id: str) -> tuple:
        """Format single product detail. Returns (text, image_url)."""
        product = await self.get_product(product_id)
        if not product:
            return "Product nahi mila! 😔", None

        lines = [f"*{product['name']}*"]
        if product.get("brand"):
            lines.append(f"🏷️ Brand: {product['brand']}")
        lines.append(f"💰 Price: ₹{product['price']}/{product.get('unit', 'pc')}")
        if product.get("description"):
            lines.append(f"\n{product['description']}")
        if product.get("category"):
            lines.append(f"\n📂 Category: {product['category']}")
        if product.get("specs"):
            lines.append("\n📋 Specs:")
            for k, v in product["specs"].items():
                lines.append(f"  • {k}: {v}")

        if product["stock"] > 0:
            lines.append(f"\n📦 Stock: {product['stock']} available")
            lines.append("\nOrder karna ho toh 'buy' bolo! 🛒")
        else:
            lines.append("\n❌ Abhi out of stock hai")

        return "\n".join(lines), product.get("image_url")

    def _product_to_dict(self, product: Product) -> dict:
        return {
            "id": product.id,
            "name": product.name,
            "sku": product.sku,
            "price": product.price,
            "cost_price": product.cost_price,
            "description": product.description,
            "category": product.category,
            "stock": product.stock_quantity,
            "is_active": product.is_active,
            "unit": product.unit or "piece",
            "image_url": product.image_url,
            "gallery": product.gallery or [],
            "brand": product.brand,
            "model": product.model,
            "warranty": product.warranty,
            "specs": product.specs or {},
            "tags": product.tags or [],
            "item_type": product.item_type or "product",
        }
