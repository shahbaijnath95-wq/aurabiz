from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from rapidfuzz import fuzz
from models import Product, Business


class InventoryManager:
    def __init__(self, db: AsyncSession = None):
        self.db = db

    async def get_products(self, business_id: str, category: str = None, low_stock: bool = False) -> list:
        if not self.db:
            return []
        query = select(Product).where(Product.business_id == business_id, Product.is_active == True)
        if category:
            query = query.where(Product.category == category)
        if low_stock:
            query = query.where(Product.stock_quantity <= Product.min_stock)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def search_products(self, business_id: str, query_text: str, limit: int = 5) -> list:
        """Customer message se product search karo - name, description, category, sku pe match.
        Uses multi-layer matching: exact ilike -> fuzzy rapidfuzz -> token sort."""
        if not self.db or not query_text.strip():
            return []
        stop_words = {"mujhe", "chahiye", "ka", "hai", "kya", "dekhao", "batao", "dikhao", "do", "dena",
                       "lena", "kharidna", "karna", "krna", "karwana", "karwa", "bhi", "mein", "se", "ko", "pe", "ke",
                       "ye", "wo", "yeh", "aur", "ya", "par", "mai", "aap", "tum", "hum", "main",
                       "price", "rate", "cost", "kitna", "kitne", "dam", "order", "buy", "karte",
                       "ho", "nahi", "bas", "abhi", "kal", "aaj", "wala", "wali", "jo", "jisse",
                       "usse", "iske", "uske", "mera", "meri", "tere", "uska", "iska",
                       "upi", "pay", "payment", "paise", "bill", "cash", "cod", "phonepe", "gpay", "googlepay",
                       "name", "naam", "tell", "about", "what", "how", "when", "where", "who",
                       "kaun", "kaisa", "kaise", "kyun", "kyunki", "matlab", "matalab",
                       "hello", "hi", "hey", "namaste", "namaskar", "thanks", "shukriya",
                       "problem", "issue", "complaint", "galti", "sawal", "sawaal",
                       "store", "shop", "dukaan", "business", "tumhara", "aapka",
                       "karwana", "karwa", "krwana", "krwaa", "karaa", "kara", "karana", "karan",
                       "ha", "ji", "haan", "han", "ok", "theek", "acha", "accha", "sahi"}
        words = [w.strip() for w in query_text.lower().split() if len(w.strip()) > 2 and w.strip() not in stop_words]
        if not words:
            return []

        # Stem matching: "repairing" -> "repair", "cleaning" -> "clean"
        stem_map = {"repairing": "repair", "cleaning": "clean", "coloring": "color", "cutting": "cut",
                     "shampooing": "shampoo", "facial": "facial", "manicure": "manicure"}
        stemmed_words = []
        for w in words:
            stemmed_words.append(stem_map.get(w, w))
        words = stemmed_words

        # Layer 1: Exact ilike match (fast SQL) - AND between words
        word_conditions = []
        for word in words:
            word_conditions.append(or_(
                Product.name.ilike(f"%{word}%"),
                Product.description.ilike(f"%{word}%"),
                Product.category.ilike(f"%{word}%"),
                Product.sku.ilike(f"%{word}%"),
            ))
        result = await self.db.execute(
            select(Product).where(
                Product.business_id == business_id,
                Product.is_active == True,
                *word_conditions,  # AND between words
            ).order_by(Product.name).limit(limit)
        )
        exact_matches = result.scalars().all()
        if exact_matches:
            return exact_matches

        # Layer 1b: Category-based match (e.g. "computer" matches "Computer Repair" category)
        for word in words:
            cat_result = await self.db.execute(
                select(Product).where(
                    Product.business_id == business_id,
                    Product.is_active == True,
                    Product.category.ilike(f"%{word}%"),
                ).limit(limit)
            )
            cat_matches = cat_result.scalars().all()
            if cat_matches:
                return cat_matches

        # Layer 2: Fuzzy match using rapidfuzz (for misspellings, Hinglish)
        all_products = await self.db.execute(
            select(Product).where(
                Product.business_id == business_id,
                Product.is_active == True,
            )
        )
        all_products = all_products.scalars().all()
        if not all_products:
            return []

        scored = []
        query_lower = query_text.lower()
        for p in all_products:
            name_lower = p.name.lower()
            cat_lower = (p.category or "").lower()
            name_words = set(name_lower.split())
            # Count how many query words appear in product name
            query_words = set(words)
            word_overlap = len(query_words & name_words)
            # Fuzzy scores
            wratio = fuzz.WRatio(query_lower, name_lower)
            partial = fuzz.partial_ratio(query_lower, name_lower)
            token_sort = fuzz.token_sort_ratio(query_lower, name_lower)
            # Bonus for word overlap (each matching word adds 15 points)
            overlap_bonus = word_overlap * 15
            score = max(wratio, partial, token_sort) + overlap_bonus
            if score >= 70:
                scored.append((score, p))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:limit]]

    async def add_product(self, business_id: str, product_data: dict) -> Product:
        product = Product(business_id=business_id, **product_data)
        self.db.add(product)
        await self.db.flush()
        return product

    async def update_stock(self, product_id: str, quantity: int, operation: str = "set") -> Optional[Product]:
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        if not product:
            return None
        if operation == "set":
            product.stock_quantity = quantity
        elif operation == "add":
            product.stock_quantity += quantity
        elif operation == "subtract":
            product.stock_quantity = max(0, product.stock_quantity - quantity)
        await self.db.flush()
        return product

    async def get_low_stock(self, business_id: str, threshold: int = 10) -> list:
        if not self.db:
            return []
        result = await self.db.execute(
            select(Product).where(
                Product.business_id == business_id,
                Product.is_active == True,
                Product.stock_quantity <= threshold,
            )
        )
        return result.scalars().all()

    async def update_inventory(self, product_id: str, data: dict) -> Optional[Product]:
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        if not product:
            return None
        for key, value in data.items():
            if hasattr(product, key):
                setattr(product, key, value)
        await self.db.flush()
        return product

    async def get_inventory_analytics(self, business_id: str) -> dict:
        products = await self.get_products(business_id)
        total_products = len(products)
        total_value = sum(p.price * p.stock_quantity for p in products)
        low_stock = sum(1 for p in products if p.stock_quantity <= p.min_stock)
        out_of_stock = sum(1 for p in products if p.stock_quantity == 0)
        categories = {}
        for p in products:
            cat = p.category or "Uncategorized"
            categories[cat] = categories.get(cat, 0) + 1
        return {
            "total_products": total_products,
            "total_value": total_value,
            "low_stock_count": low_stock,
            "out_of_stock_count": out_of_stock,
            "categories": categories,
        }

    async def create_reorder_alert(self, business_id: str, product_id: str, threshold: int) -> dict:
        return {
            "business_id": business_id,
            "product_id": product_id,
            "threshold": threshold,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
        }

    async def check_reorder_alerts(self, business_id: str) -> list:
        products = await self.get_low_stock(business_id)
        return [
            {"product_id": p.id, "name": p.name, "stock": p.stock_quantity, "min_stock": p.min_stock}
            for p in products
        ]

    async def bulk_update(self, business_id: str, updates: list) -> dict:
        results = []
        for update in updates:
            product_id = update.get("product_id")
            quantity = update.get("quantity", 0)
            operation = update.get("operation", "set")
            product = await self.update_stock(product_id, quantity, operation)
            results.append({"product_id": product_id, "success": product is not None})
        return {"updated": sum(1 for r in results if r["success"]), "total": len(results)}

    async def get_turnover_rate(self, business_id: str) -> dict:
        return {"business_id": business_id, "turnover_rate": 0.0, "period": "monthly"}

    async def get_dead_stock(self, business_id: str) -> list:
        return []
