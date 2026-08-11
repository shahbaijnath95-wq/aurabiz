from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models import Invoice, Business, Transaction, Customer
import uuid


class BillingService:
    def __init__(self, db: AsyncSession = None):
        self.db = db

    TIER_PRICES = {
        "starter": 999,
        "growth": 2499,
        "enterprise": 4999,
    }

    TIER_LIMITS = {
        "starter": {"messages": 500, "products": 100, "users": 1},
        "growth": {"messages": 2500, "products": 500, "users": 5},
        "enterprise": {"messages": 0, "products": 0, "users": 0},  # 0 = unlimited
    }

    async def create_invoice(self, business_id: str, amount: float, description: str) -> Invoice:
        invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m')}-{str(uuid.uuid4())[:6].upper()}"
        invoice = Invoice(
            business_id=business_id,
            number=invoice_number,
            total=amount,
            subtotal=amount,
            items=[{"description": description, "amount": amount}],
            status="draft",
            due_at=datetime.utcnow() + timedelta(days=30),
        )
        self.db.add(invoice)
        await self.db.flush()
        return invoice

    async def process_payment(self, invoice_id: str, payment_method: str) -> dict:
        result = await self.db.execute(select(Invoice).where(Invoice.id == invoice_id))
        invoice = result.scalar_one_or_none()
        if not invoice:
            return {"error": "Invoice nahi mili"}
        invoice.status = "paid"
        invoice.paid_at = datetime.utcnow()
        invoice.notes = (invoice.notes or "") + f"\nPayment method: {payment_method}"
        await self.db.flush()
        return {"invoice_id": invoice_id, "status": "paid", "payment_method": payment_method}

    async def check_subscription_status(self, business_id: str) -> dict:
        result = await self.db.execute(select(Business).where(Business.id == business_id))
        business = result.scalar_one_or_none()
        if not business:
            return {"error": "Business nahi mili"}
        return {
            "business_id": business_id,
            "tier": business.subscription_tier,
            "status": business.subscription_status,
            "trial_ends_at": str(business.trial_ends_at) if business.trial_ends_at else None,
        }

    async def upgrade_tier(self, business_id: str, new_tier: str) -> dict:
        result = await self.db.execute(select(Business).where(Business.id == business_id))
        business = result.scalar_one_or_none()
        if not business:
            return {"error": "Business nahi mili"}
        business.subscription_tier = new_tier
        await self.db.flush()
        return {"business_id": business_id, "new_tier": new_tier, "price": self.TIER_PRICES.get(new_tier, 0)}

    async def generate_usage_report(self, business_id: str) -> dict:
        return {
            "business_id": business_id,
            "messages_used": 0,
            "messages_limit": -1,
            "users_used": 1,
            "users_limit": 1,
            "billing_period": "current_month",
        }

    async def check_message_quota(self, business_id: str) -> dict:
        from models import WhatsAppMessage
        result = await self.db.execute(select(Business).where(Business.id == business_id))
        business = result.scalar_one_or_none()
        if not business:
            return {"remaining": 0, "limit": 0, "tier": "none"}
        tier = business.subscription_tier or "starter"
        limits = self.TIER_LIMITS.get(tier, self.TIER_LIMITS["starter"])
        msg_limit = limits.get("messages", 500)
        # Enterprise (0 = unlimited) — skip check
        if msg_limit == 0:
            return {"remaining": -1, "limit": -1, "tier": tier, "unlimited": True}
        # Count this month's inbound messages
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        count_result = await self.db.execute(
            select(func.count(WhatsAppMessage.id)).where(
                WhatsAppMessage.business_id == business_id,
                WhatsAppMessage.direction == "inbound",
                WhatsAppMessage.created_at >= month_start,
            )
        )
        used = count_result.scalar() or 0
        remaining = max(0, msg_limit - used)
        return {"remaining": remaining, "limit": msg_limit, "tier": tier, "used": used, "unlimited": False}

    async def increment_message_count(self, business_id: str) -> dict:
        quota = await self.check_message_quota(business_id)
        if quota.get("unlimited"):
            return {"status": "ok", "remaining": -1}
        if quota["remaining"] <= 0:
            return {"error": "Message quota khatam ho gaya hai. Plan upgrade karein.", "tier": quota["tier"]}
        return {"status": "ok", "remaining": quota["remaining"] - 1}

    async def suspend_overdue_accounts(self) -> int:
        return 0
