from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid
import qrcode
from io import BytesIO
import base64


def generate_uuid():
    return str(uuid.uuid4())


class PaymentManager:
    def __init__(self, db: AsyncSession = None):
        self.db = db

    async def get_payments(self, business_id: str = None, page: int = 1, limit: int = 20) -> dict:
        from models import Payment
        if not self.db:
            return {"payments": [], "total": 0}

        total_result = await self.db.execute(select(func.count(Payment.id)))
        total = total_result.scalar() or 0

        offset = (page - 1) * limit
        query = select(Payment)
        if business_id:
            query = query.where(Payment.business_id == business_id)
        query = query.offset(offset).limit(limit).order_by(Payment.created_at.desc())
        result = await self.db.execute(query)
        payments = result.scalars().all()

        return {
            "payments": [
                {
                    "id": p.id, "amount": p.amount, "currency": p.currency,
                    "payment_method": p.payment_method, "status": p.status,
                    "customer_id": p.customer_id, "business_id": p.business_id,
                    "reference": p.reference, "notes": p.notes,
                    "created_at": str(p.created_at), "updated_at": str(p.updated_at),
                }
                for p in payments
            ],
            "total": total,
            "page": page,
            "limit": limit,
        }

    async def update_payment_status(self, payment_id: str, status: str, user_id: str = None) -> Optional[dict]:
        from models import Payment
        if not self.db:
            return None

        result = await self.db.execute(select(Payment).where(Payment.id == payment_id))
        payment = result.scalar_one_or_none()
        if not payment:
            return None

        payment.status = status
        payment.updated_at = datetime.utcnow()
        await self.db.flush()

        return {
            "id": payment.id, "amount": payment.amount, "status": payment.status,
            "payment_method": payment.payment_method, "updated_at": str(payment.updated_at),
        }

    async def generate_qr_payment(self, business_id: str, amount: float, customer_name: str = None,
                                   customer_email: str = None, customer_phone: str = None) -> dict:
        from models import Payment
        if not self.db:
            raise ValueError("Database not available")

        payment_id = generate_uuid()
        payment = Payment(
            id=payment_id,
            business_id=business_id,
            amount=amount,
            currency="INR",
            payment_method="qr",
            status="pending",
            notes=f"QR Payment - {customer_name or 'Walk-in Customer'}",
        )
        self.db.add(payment)
        await self.db.flush()

        qr = qrcode.make(f"upi://pay?pa=merchant@upi&pn=WhatsApp+Shop&am={amount}&currency=INR&tn=Payment+{payment_id[:8]}")
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return {
            "payment_id": payment_id,
            "qr_code": f"data:image/png;base64,{qr_base64}",
            "amount": amount,
            "status": "pending",
        }
