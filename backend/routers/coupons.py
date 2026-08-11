"""Coupon management - create, validate, apply coupons."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from database import get_db
from models import Coupon, User
from schemas import CouponCreate, CouponResponse
from auth import get_current_user, verify_business_access

router = APIRouter(prefix="/api/v1", tags=["coupons"])


@router.post("/coupons")
async def create_coupon(req: CouponCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, req.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    coupon = Coupon(
        business_id=req.business_id,
        code=req.code.upper(),
        discount_type=req.discount_type,
        discount_value=req.discount_value,
        min_order=req.min_order,
        max_uses=req.max_uses,
        expires_at=req.expires_at,
    )
    db.add(coupon)
    await db.commit()
    return {"status": "created", "coupon_id": coupon.id, "code": coupon.code}


@router.get("/coupons/{business_id}")
async def list_coupons(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(
        select(Coupon).where(Coupon.business_id == business_id).order_by(Coupon.created_at.desc())
    )
    coupons = result.scalars().all()
    return {"coupons": [
        {
            "id": c.id, "code": c.code, "discount_type": c.discount_type,
            "discount_value": c.discount_value, "min_order": c.min_order,
            "max_uses": c.max_uses, "used_count": c.used_count,
            "is_active": c.is_active,
            "expires_at": str(c.expires_at) if c.expires_at else None,
            "created_at": str(c.created_at) if c.created_at else None,
        }
        for c in coupons
    ]}


@router.post("/coupons/validate")
async def validate_coupon(code: str, business_id: str, order_amount: float = 0, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(
        select(Coupon).where(
            Coupon.business_id == business_id,
            Coupon.code == code.upper(),
            Coupon.is_active == True,
        )
    )
    coupon = result.scalar_one_or_none()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon nahi mila")

    if coupon.expires_at and coupon.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Coupon expire ho gaya hai")

    if coupon.used_count >= coupon.max_uses:
        raise HTTPException(status_code=400, detail="Coupon usage khatam ho gaya")

    if order_amount < coupon.min_order:
        raise HTTPException(status_code=400, detail=f"Minimum order ₹{coupon.min_order} hai")

    if coupon.discount_type == "percent":
        discount = order_amount * coupon.discount_value / 100
    else:
        discount = coupon.discount_value

    return {
        "valid": True,
        "code": coupon.code,
        "discount_type": coupon.discount_type,
        "discount_value": coupon.discount_value,
        "discount_amount": round(discount, 2),
        "final_amount": round(order_amount - discount, 2),
    }


@router.put("/coupons/{coupon_id}")
async def update_coupon(coupon_id: str, is_active: bool = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Coupon).where(Coupon.id == coupon_id))
    coupon = result.scalar_one_or_none()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon nahi mila")
    if not await verify_business_access(current_user, coupon.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    if is_active is not None:
        coupon.is_active = is_active
    await db.commit()
    return {"status": "updated"}


@router.delete("/coupons/{coupon_id}")
async def delete_coupon(coupon_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Coupon).where(Coupon.id == coupon_id))
    coupon = result.scalar_one_or_none()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon nahi mila")
    if not await verify_business_access(current_user, coupon.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    await db.delete(coupon)
    await db.commit()
    return {"status": "deleted"}
