"""
Payments Router — UPI payment link generation, QR codes, payment tracking.
Supports UPI deeplinks for WhatsApp sharing.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger
import qrcode
from io import BytesIO
import base64
import urllib.parse

from database import get_db
from auth import get_current_user, verify_business_access
from models import User, Payment, Business
from services.payment_manager import PaymentManager

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


@router.get("/{business_id}")
async def get_payments(
    business_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get paginated payment list."""
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        pm = PaymentManager(db)
        result = await pm.get_payments(page, limit)
        return result
    except Exception as e:
        logger.error("Payments fetch error: {}", e)
        return {"payments": [], "total": 0, "page": page, "limit": limit}


@router.post("/{business_id}/link")
async def create_payment_link(
    business_id: str,
    amount: float,
    customer_name: str = Query(None),
    customer_phone: str = Query(None),
    description: str = Query(None),
    upi_id: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a UPI payment link for WhatsApp sharing."""
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        # Get business UPI ID from settings or use provided one
        if not upi_id:
            from models import BusinessSettings
            settings_result = await db.execute(
                select(BusinessSettings).where(
                    BusinessSettings.business_id == business_id,
                    BusinessSettings.section == "payments",
                )
            )
            settings = settings_result.scalar_one_or_none()
            if settings and settings.data:
                upi_id = settings.data.get("upi_id", "merchant@upi")
            else:
                upi_id = "merchant@upi"

        # Create payment record
        pm = PaymentManager(db)
        payment_id = str(__import__('uuid').uuid4())
        payment = Payment(
            id=payment_id,
            business_id=business_id,
            amount=amount,
            currency="INR",
            payment_method="upi_link",
            status="pending",
            notes=description or f"Payment link for {customer_name or 'customer'}",
        )
        db.add(payment)
        await db.flush()

        # Get business name
        biz_result = await db.execute(select(Business).where(Business.id == business_id))
        business = biz_result.scalar_one_or_none()
        business_name = business.name if business else "Business"

        # Generate UPI deeplink
        tn = description or f"Payment to {business_name}"
        upi_params = {
            "pa": upi_id,
            "pn": business_name,
            "am": str(amount),
            "currency": "INR",
            "tn": tn,
            "tr": payment_id[:16],
        }
        upi_link = "upi://pay?" + urllib.parse.urlencode(upi_params)

        # Generate QR code
        qr = qrcode.make(upi_link)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return {
            "payment_id": payment_id,
            "upi_link": upi_link,
            "qr_code": f"data:image/png;base64,{qr_base64}",
            "amount": amount,
            "currency": "INR",
            "upi_id": upi_id,
            "status": "pending",
            "message": f"UPI payment link ready! Amount: ₹{amount}",
        }
    except Exception as e:
        logger.error("Payment link error: {}", e)
        raise HTTPException(status_code=500, detail=f"Payment link generate nahi ho paya: {str(e)}")


@router.post("/{business_id}/link/whatsapp")
async def create_whatsapp_payment_message(
    business_id: str,
    amount: float,
    customer_name: str = Query(None),
    description: str = Query(None),
    upi_id: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate payment link and WhatsApp message text."""
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        # Reuse the link generation logic
        link_result = await create_payment_link(
            business_id, amount, customer_name, None, description, upi_id, db, current_user
        )

        # Format WhatsApp message
        wa_msg = (
            f"💳 *Payment Request*\n\n"
            f"Amount: ₹{amount}\n"
            f"Description: {description or 'Payment'}\n\n"
            f"UPI Payment karne ke liye neeche click karein:\n"
            f"{link_result['upi_link']}\n\n"
            f"Ya QR code scan karein 👆"
        )

        return {
            **link_result,
            "whatsapp_message": wa_msg,
        }
    except Exception as e:
        logger.error("WhatsApp payment message error: {}", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{payment_id}/status")
async def update_payment_status(
    payment_id: str,
    status: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update payment status."""
    payment_result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = payment_result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment nahi mila")
    if not await verify_business_access(current_user, payment.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    pm = PaymentManager(db)
    result = await pm.update_payment_status(payment_id, status)
    if not result:
        raise HTTPException(status_code=404, detail="Payment nahi mila")
    return result


@router.get("/{business_id}/stats")
async def get_payment_stats(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get payment statistics."""
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        from sqlalchemy import case
        from datetime import datetime, timedelta

        week_ago = datetime.utcnow() - timedelta(days=7)

        result = await db.execute(
            select(
                func.count(Payment.id).label("total"),
                func.sum(Payment.amount).label("total_amount"),
                func.count(case((Payment.status == "completed", 1))).label("completed"),
                func.count(case((Payment.status == "pending", 1))).label("pending"),
                func.count(case((Payment.status == "failed", 1))).label("failed"),
            ).where(
                Payment.business_id == business_id,
            )
        )
        row = result.one_or_none()

        # This week stats
        week_result = await db.execute(
            select(
                func.count(Payment.id).label("count"),
                func.sum(Payment.amount).label("amount"),
            ).where(
                Payment.business_id == business_id,
                Payment.created_at >= week_ago,
            )
        )
        week_row = week_result.one_or_none()

        return {
            "total_payments": row.total if row else 0,
            "total_amount": float(row.total_amount or 0),
            "completed": row.completed if row else 0,
            "pending": row.pending if row else 0,
            "failed": row.failed if row else 0,
            "this_week": {
                "count": week_row.count if week_row else 0,
                "amount": float(week_row.amount or 0),
            },
        }
    except Exception as e:
        logger.error("Payment stats error: {}", e)
        return {"total_payments": 0, "total_amount": 0, "completed": 0, "pending": 0, "failed": 0}
