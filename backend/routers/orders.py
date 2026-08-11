"""Order management - CRUD, status tracking, delivery management."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from io import BytesIO

from database import get_db
from models import Order, Customer, User, Business
from schemas import OrderCreate, OrderUpdate
from auth import get_current_user, verify_business_access
from services.invoice_pdf import generate_invoice_pdf

router = APIRouter(prefix="/api/v1", tags=["orders"])


@router.post("/orders")
async def create_order(req: OrderCreate, db: AsyncSession = Depends(get_db)):
    order = Order(
        business_id=req.business_id,
        customer_id=req.customer_id,
        customer_name=req.customer_name,
        customer_phone=req.customer_phone,
        product_id=req.product_id,
        product_name=req.product_name,
        quantity=req.quantity,
        unit_price=req.unit_price,
        total_price=req.total_price,
        discount_amount=req.discount_amount,
        coupon_code=req.coupon_code,
        delivery_type=req.delivery_type,
        delivery_address=req.delivery_address,
        delivery_fee=req.delivery_fee,
        notes=req.notes,
        status="pending",
    )
    db.add(order)

    if req.customer_id:
        cust_result = await db.execute(select(Customer).where(Customer.id == req.customer_id))
        customer = cust_result.scalar_one_or_none()
        if customer:
            customer.total_orders = (customer.total_orders or 0) + 1
            customer.total_spent = (customer.total_spent or 0) + req.total_price

    await db.commit()
    return {"status": "created", "order_id": order.id}


@router.get("/orders/{business_id}")
async def list_orders(business_id: str, status: str = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(Order).where(Order.business_id == business_id)
    if status:
        query = query.where(Order.status == status)
    result = await db.execute(query.order_by(desc(Order.created_at)).limit(100))
    orders = result.scalars().all()
    return {"orders": [
        {
            "id": o.id, "customer_name": o.customer_name, "customer_phone": o.customer_phone,
            "product_name": o.product_name, "quantity": o.quantity, "unit_price": o.unit_price,
            "total_price": o.total_price, "discount_amount": o.discount_amount,
            "coupon_code": o.coupon_code, "delivery_type": o.delivery_type,
            "delivery_address": o.delivery_address, "delivery_fee": o.delivery_fee,
            "status": o.status, "notes": o.notes,
            "created_at": str(o.created_at) if o.created_at else None,
            "updated_at": str(o.updated_at) if o.updated_at else None,
        }
        for o in orders
    ]}


@router.get("/orders/{business_id}/stats")
async def order_stats(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Order).where(Order.business_id == business_id))
    orders = list(result.scalars().all())
    total = len(orders)
    pending = sum(1 for o in orders if o.status == "pending")
    delivered = sum(1 for o in orders if o.status == "delivered")
    cancelled = sum(1 for o in orders if o.status == "cancelled")
    total_revenue = sum(o.total_price for o in orders if o.status in ("confirmed", "delivered"))
    return {"total": total, "pending": pending, "delivered": delivered, "cancelled": cancelled, "total_revenue": round(total_revenue, 2)}


@router.put("/orders/{order_id}")
async def update_order(order_id: str, req: OrderUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order nahi mila")
    if req.status:
        order.status = req.status
    if req.notes:
        order.notes = req.notes
    order.updated_at = datetime.utcnow()
    await db.commit()
    return {"status": "updated", "order_status": order.status}


@router.get("/orders/{order_id}/invoice")
async def download_invoice(order_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order nahi mila")

    biz_name = "My Business"
    biz_address = ""
    biz_phone = ""

    try:
        biz_result = await db.execute(select(Business).where(Business.id == order.business_id))
        business = biz_result.scalar_one_or_none()
        if business:
            biz_name = business.name or "My Business"
            biz_address = business.address or ""
            biz_phone = business.phone_number or ""
    except Exception:
        pass

    try:
        invoice_num = f"INV-{order.created_at.strftime('%Y%m%d')}-{order.id[:8].upper()}"
    except Exception:
        invoice_num = f"INV-{order.id[:8].upper()}"

    order_dict = {
        "customer_name": order.customer_name or "Customer",
        "customer_phone": order.customer_phone or "",
        "product_name": order.product_name,
        "quantity": order.quantity,
        "unit_price": order.unit_price,
        "total_price": order.total_price,
        "discount_amount": order.discount_amount or 0,
        "coupon_code": order.coupon_code or "",
        "delivery_type": order.delivery_type or "pickup",
        "delivery_address": order.delivery_address or "",
        "delivery_fee": order.delivery_fee or 0,
        "status": order.status or "pending",
    }

    pdf_bytes = generate_invoice_pdf(
        invoice_number=invoice_num,
        order=order_dict,
        business_name=biz_name,
        business_address=biz_address,
        business_phone=biz_phone,
        notes=order.notes or "",
    )

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={invoice_num}.pdf"},
    )


@router.get("/orders/{order_id}/payment-link")
async def get_payment_link(order_id: str, db: AsyncSession = Depends(get_db)):
    """Public endpoint - order details for payment page."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order nahi mila")

    total = (order.total_price or 0) - (order.discount_amount or 0) + (order.delivery_fee or 0)

    return {
        "order_id": order.id,
        "amount": round(total, 2),
        "product_name": order.product_name,
        "customer_name": order.customer_name or "Customer",
        "customer_phone": order.customer_phone or "",
        "status": order.status,
        "business_id": order.business_id,
        "delivery_type": order.delivery_type or "pickup",
    }


