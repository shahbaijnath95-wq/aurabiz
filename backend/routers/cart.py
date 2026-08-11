"""Cart management - add, remove, checkout."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import CartItem, Product, User
from schemas import CartItemCreate
from auth import get_current_user, verify_business_access

router = APIRouter(prefix="/api/v1", tags=["cart"])


@router.post("/cart")
async def add_to_cart(req: CartItemCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, req.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    existing = await db.execute(
        select(CartItem).where(
            CartItem.business_id == req.business_id,
            CartItem.customer_id == req.customer_id,
            CartItem.product_id == req.product_id,
        )
    )
    cart_item = existing.scalar_one_or_none()
    if cart_item:
        cart_item.quantity += req.quantity
    else:
        cart_item = CartItem(
            business_id=req.business_id,
            customer_id=req.customer_id,
            product_id=req.product_id,
            quantity=req.quantity,
        )
        db.add(cart_item)
    await db.commit()
    return {"status": "added", "cart_item_id": cart_item.id, "quantity": cart_item.quantity}


@router.get("/cart/{business_id}/{customer_id}")
async def get_cart(business_id: str, customer_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(
        select(CartItem).where(CartItem.business_id == business_id, CartItem.customer_id == customer_id)
    )
    items = result.scalars().all()
    cart_data = []
    total = 0
    for item in items:
        prod_result = await db.execute(select(Product).where(Product.id == item.product_id))
        prod = prod_result.scalar_one_or_none()
        if prod:
            item_total = prod.price * item.quantity
            total += item_total
            cart_data.append({
                "id": item.id, "product_id": item.product_id,
                "product_name": prod.name, "quantity": item.quantity,
                "unit_price": prod.price, "total_price": item_total,
            })
    return {"items": cart_data, "total": round(total, 2), "item_count": len(cart_data)}


@router.put("/cart/{cart_item_id}")
async def update_cart_item(cart_item_id: str, quantity: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(CartItem).where(CartItem.id == cart_item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item nahi mila")
    if not await verify_business_access(current_user, item.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    if quantity <= 0:
        await db.delete(item)
    else:
        item.quantity = quantity
    await db.commit()
    return {"status": "updated"}


@router.delete("/cart/{cart_item_id}")
async def remove_from_cart(cart_item_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(CartItem).where(CartItem.id == cart_item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item nahi mila")
    if not await verify_business_access(current_user, item.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    await db.delete(item)
    await db.commit()
    return {"status": "removed"}


@router.delete("/cart/{business_id}/{customer_id}")
async def clear_cart(business_id: str, customer_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(
        select(CartItem).where(CartItem.business_id == business_id, CartItem.customer_id == customer_id)
    )
    items = result.scalars().all()
    for item in items:
        await db.delete(item)
    await db.commit()
    return {"status": "cleared"}

