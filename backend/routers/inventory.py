from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from auth import get_current_user, verify_business_access
from models import User, Business, Product
from schemas import ProductCreate, ProductUpdate, StockUpdate, BulkStockUpdate, SuccessResponse
from services.inventory_manager import InventoryManager

router = APIRouter(prefix="/api/v1/inventory", tags=["Inventory"])


@router.get("/{business_id}")
async def list_products(
    business_id: str,
    category: str = Query(None),
    low_stock: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    im = InventoryManager(db)
    products = await im.get_products(business_id, category, low_stock)
    return {
        "products": [
            {
                "id": p.id, "name": p.name, "sku": p.sku, "price": p.price,
                "stock_quantity": p.stock_quantity, "category": p.category,
                "is_active": p.is_active, "min_stock": p.min_stock,
                "item_type": getattr(p, "item_type", None) or "product",
                "duration_minutes": getattr(p, "duration_minutes", None),
                "brand": getattr(p, "brand", None),
                "model": getattr(p, "model", None),
                "warranty": getattr(p, "warranty", None),
                "hsn_code": getattr(p, "hsn_code", None),
                "gst_rate": getattr(p, "gst_rate", 0),
                "tags": getattr(p, "tags", []),
                "specs": getattr(p, "specs", {}),
                "image_url": getattr(p, "image_url", None),
                "gallery": getattr(p, "gallery", []),
                "description": getattr(p, "description", None),
                "cost_price": getattr(p, "cost_price", None),
                "unit": getattr(p, "unit", "piece"),
            }
            for p in products
        ]
    }


@router.post("/products")
async def add_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, data.business_id, db):
        raise HTTPException(status_code=403, detail='Access denied')
    im = InventoryManager(db)
    product = await im.add_product(data.business_id, data.model_dump(exclude={"business_id"}))
    return {"status": "created", "product_id": product.id}


@router.put("/products/{id}")
async def update_product(
    id: str,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify product ownership
    from models import Product
    from sqlalchemy import select as sql_select
    prod_result = await db.execute(sql_select(Product).where(Product.id == id))
    product_check = prod_result.scalar_one_or_none()
    if product_check and not await verify_business_access(current_user, product_check.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    im = InventoryManager(db)
    product = await im.update_inventory(id, data.model_dump(exclude_unset=True))
    if not product:
        raise HTTPException(status_code=404, detail="Product nahi mila")
    return {"status": "updated", "product_id": product.id}


@router.delete("/products/{id}")
async def delete_product(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify product ownership
    from models import Product
    from sqlalchemy import select as sql_select
    prod_result = await db.execute(sql_select(Product).where(Product.id == id))
    product_check = prod_result.scalar_one_or_none()
    if product_check and not await verify_business_access(current_user, product_check.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    im = InventoryManager(db)
    product = await im.update_inventory(id, {"is_active": False})
    return {"status": "deleted"}


@router.put("/products/{id}/stock")
async def update_stock(
    id: str,
    data: StockUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    im = InventoryManager(db)
    product = await im.update_stock(id, data.quantity, data.operation)
    if not product:
        raise HTTPException(status_code=404, detail="Product nahi mila")
    return {"status": "updated", "product_id": product.id, "new_stock": product.stock_quantity}


@router.get("/low-stock/{business_id}")
async def low_stock(
    business_id: str,
    threshold: int = Query(10),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    im = InventoryManager(db)
    products = await im.get_low_stock(business_id, threshold)
    return {"products": [{"id": p.id, "name": p.name, "stock": p.stock_quantity, "min_stock": p.min_stock} for p in products]}


@router.post("/bulk-update")
async def bulk_update(
    data: BulkStockUpdate,
    business_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    im = InventoryManager(db)
    return await im.bulk_update(business_id, data.updates)


@router.get("/analytics/{business_id}")
async def inventory_analytics(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    im = InventoryManager(db)
    return await im.get_inventory_analytics(business_id)


@router.post("/reorder-alerts")
async def set_reorder_alerts(
    business_id: str = Query(...),
    product_id: str = Query(...),
    threshold: int = Query(10),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    im = InventoryManager(db)
    return await im.create_reorder_alert(business_id, product_id, threshold)


