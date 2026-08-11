from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import ScheduledMessage, Customer
from datetime import datetime, timedelta, timezone


class ScheduledMessageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_message(self, business_id: str, content: str, customer_id: str = None,
                             message_type: str = "text", template_name: str = None,
                             template_vars: dict = None, scheduled_for: datetime = None) -> ScheduledMessage:
        msg = ScheduledMessage(
            business_id=business_id,
            customer_id=customer_id,
            content=content,
            message_type=message_type,
            template_name=template_name,
            template_vars=template_vars or {},
            scheduled_for=scheduled_for or datetime.now(timezone.utc) + timedelta(hours=1),
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def list_messages(self, business_id: str, status: str = None) -> list[ScheduledMessage]:
        query = select(ScheduledMessage).where(ScheduledMessage.business_id == business_id)
        if status:
            query = query.where(ScheduledMessage.status == status)
        query = query.order_by(ScheduledMessage.scheduled_for.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_message(self, message_id: str) -> ScheduledMessage | None:
        result = await self.db.execute(select(ScheduledMessage).where(ScheduledMessage.id == message_id))
        return result.scalar_one_or_none()

    async def update_message(self, message_id: str, **kwargs) -> ScheduledMessage | None:
        msg = await self.get_message(message_id)
        if not msg:
            return None
        if msg.status != "pending":
            return None
        for k, v in kwargs.items():
            if v is not None and hasattr(msg, k):
                setattr(msg, k, v)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def cancel_message(self, message_id: str) -> ScheduledMessage | None:
        msg = await self.get_message(message_id)
        if not msg or msg.status != "pending":
            return None
        msg.status = "cancelled"
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def delete_message(self, message_id: str) -> bool:
        msg = await self.get_message(message_id)
        if not msg:
            return False
        await self.db.delete(msg)
        await self.db.commit()
        return True

    async def get_pending_messages(self, business_id: str = None) -> list[ScheduledMessage]:
        now = datetime.now(timezone.utc)
        query = select(ScheduledMessage).where(
            ScheduledMessage.status == "pending",
            ScheduledMessage.scheduled_for <= now,
        )
        if business_id:
            query = query.where(ScheduledMessage.business_id == business_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def mark_sent(self, message_id: str) -> ScheduledMessage | None:
        msg = await self.get_message(message_id)
        if not msg:
            return None
        msg.status = "sent"
        msg.sent_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def mark_failed(self, message_id: str, error: str) -> ScheduledMessage | None:
        msg = await self.get_message(message_id)
        if not msg:
            return None
        msg.status = "failed"
        msg.error_message = error
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def get_message_stats(self, business_id: str) -> dict:
        total = await self.db.execute(
            select(func.count(ScheduledMessage.id)).where(ScheduledMessage.business_id == business_id)
        )
        pending = await self.db.execute(
            select(func.count(ScheduledMessage.id)).where(
                ScheduledMessage.business_id == business_id, ScheduledMessage.status == "pending"
            )
        )
        sent = await self.db.execute(
            select(func.count(ScheduledMessage.id)).where(
                ScheduledMessage.business_id == business_id, ScheduledMessage.status == "sent"
            )
        )
        failed = await self.db.execute(
            select(func.count(ScheduledMessage.id)).where(
                ScheduledMessage.business_id == business_id, ScheduledMessage.status == "failed"
            )
        )
        return {
            "total": total.scalar() or 0,
            "pending": pending.scalar() or 0,
            "sent": sent.scalar() or 0,
            "failed": failed.scalar() or 0,
        }
