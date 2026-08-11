from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import FollowUp, Customer
from datetime import datetime, timedelta, timezone


class FollowUpService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_followup(self, business_id: str, message_template: str, customer_id: str = None,
                              trigger_type: str = "custom", trigger_reference_id: str = None,
                              delay_hours: int = 24) -> FollowUp:
        followup = FollowUp(
            business_id=business_id,
            customer_id=customer_id,
            trigger_type=trigger_type,
            trigger_reference_id=trigger_reference_id,
            message_template=message_template,
            delay_hours=delay_hours,
            scheduled_for=datetime.now(timezone.utc) + timedelta(hours=delay_hours),
        )
        self.db.add(followup)
        await self.db.commit()
        await self.db.refresh(followup)
        return followup

    async def auto_create_order_followup(self, business_id: str, customer_id: str, order_id: str, product_name: str) -> FollowUp:
        msg = f"Hi! Aapka order '{product_name}' deliver ho gaya. Kaisa laga? Agar koi feedback ho toh bataiye! 🙏"
        return await self.create_followup(
            business_id=business_id,
            customer_id=customer_id,
            trigger_type="order_completed",
            trigger_reference_id=order_id,
            message_template=msg,
            delay_hours=24,
        )

    async def auto_create_appointment_followup(self, business_id: str, customer_id: str, booking_id: str, service_name: str) -> FollowUp:
        msg = f"Hi! Aapka appointment '{service_name}' ho gaya. Kaisa raha experience? Zaroor batayein! 😊"
        return await self.create_followup(
            business_id=business_id,
            customer_id=customer_id,
            trigger_type="appointment",
            trigger_reference_id=booking_id,
            message_template=msg,
            delay_hours=48,
        )

    async def auto_create_review_followup(self, business_id: str, customer_id: str, order_id: str) -> FollowUp:
        msg = "Hi! Hum aapse feedback lena chahte hain. Aap hamare service se khush hain? ⭐"
        return await self.create_followup(
            business_id=business_id,
            customer_id=customer_id,
            trigger_type="review",
            trigger_reference_id=order_id,
            message_template=msg,
            delay_hours=72,
        )

    async def list_followups(self, business_id: str, status: str = None) -> list[FollowUp]:
        query = select(FollowUp).where(FollowUp.business_id == business_id)
        if status:
            query = query.where(FollowUp.status == status)
        query = query.order_by(FollowUp.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_pending_followups(self, business_id: str) -> list[FollowUp]:
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(FollowUp).where(
                FollowUp.business_id == business_id,
                FollowUp.status == "pending",
                FollowUp.scheduled_for <= now,
            )
        )
        return result.scalars().all()

    async def mark_sent(self, followup_id: str) -> FollowUp | None:
        result = await self.db.execute(select(FollowUp).where(FollowUp.id == followup_id))
        fu = result.scalar_one_or_none()
        if not fu:
            return None
        fu.status = "sent"
        fu.sent_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(fu)
        return fu

    async def mark_failed(self, followup_id: str, error: str) -> FollowUp | None:
        result = await self.db.execute(select(FollowUp).where(FollowUp.id == followup_id))
        fu = result.scalar_one_or_none()
        if not fu:
            return None
        fu.status = "failed"
        fu.error_message = error
        await self.db.commit()
        await self.db.refresh(fu)
        return fu

    async def cancel_followup(self, followup_id: str) -> FollowUp | None:
        result = await self.db.execute(select(FollowUp).where(FollowUp.id == followup_id))
        fu = result.scalar_one_or_none()
        if not fu:
            return None
        fu.status = "cancelled"
        await self.db.commit()
        await self.db.refresh(fu)
        return fu

    async def update_followup(self, followup_id: str, **kwargs) -> FollowUp | None:
        result = await self.db.execute(select(FollowUp).where(FollowUp.id == followup_id))
        fu = result.scalar_one_or_none()
        if not fu:
            return None
        for k, v in kwargs.items():
            if v is not None and hasattr(fu, k):
                setattr(fu, k, v)
        await self.db.commit()
        await self.db.refresh(fu)
        return fu

    async def delete_followup(self, followup_id: str) -> bool:
        result = await self.db.execute(select(FollowUp).where(FollowUp.id == followup_id))
        fu = result.scalar_one_or_none()
        if not fu:
            return False
        await self.db.delete(fu)
        await self.db.commit()
        return True

    async def get_followup_stats(self, business_id: str) -> dict:
        total = await self.db.execute(
            select(func.count(FollowUp.id)).where(FollowUp.business_id == business_id)
        )
        pending = await self.db.execute(
            select(func.count(FollowUp.id)).where(FollowUp.business_id == business_id, FollowUp.status == "pending")
        )
        sent = await self.db.execute(
            select(func.count(FollowUp.id)).where(FollowUp.business_id == business_id, FollowUp.status == "sent")
        )
        failed = await self.db.execute(
            select(func.count(FollowUp.id)).where(FollowUp.business_id == business_id, FollowUp.status == "failed")
        )
        return {
            "total": total.scalar() or 0,
            "pending": pending.scalar() or 0,
            "sent": sent.scalar() or 0,
            "failed": failed.scalar() or 0,
        }
