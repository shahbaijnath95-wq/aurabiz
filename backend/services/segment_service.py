from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession
from models import Segment, CustomerSegment, Customer, Transaction, Order
from datetime import datetime, timedelta, timezone
import json


class SegmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_segment(self, business_id: str, name: str, description: str = None,
                             rules: list = None, rule_operator: str = "and",
                             is_dynamic: bool = True) -> Segment:
        segment = Segment(
            business_id=business_id,
            name=name,
            description=description,
            rules=rules or [],
            rule_operator=rule_operator,
            is_dynamic=is_dynamic,
        )
        self.db.add(segment)
        await self.db.flush()
        if rules:
            count = await self._compute_segment_count(business_id, rules, rule_operator)
            segment.customer_count = count
        await self.db.commit()
        await self.db.refresh(segment)
        return segment

    async def list_segments(self, business_id: str) -> list[Segment]:
        result = await self.db.execute(
            select(Segment).where(Segment.business_id == business_id).order_by(Segment.created_at.desc())
        )
        return result.scalars().all()

    async def get_segment(self, segment_id: str) -> Segment | None:
        result = await self.db.execute(select(Segment).where(Segment.id == segment_id))
        return result.scalar_one_or_none()

    async def update_segment(self, segment_id: str, **kwargs) -> Segment | None:
        segment = await self.get_segment(segment_id)
        if not segment:
            return None
        for k, v in kwargs.items():
            if v is not None and hasattr(segment, k):
                setattr(segment, k, v)
        if segment.rules:
            count = await self._compute_segment_count(segment.business_id, segment.rules, segment.rule_operator)
            segment.customer_count = count
        segment.last_refreshed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(segment)
        return segment

    async def delete_segment(self, segment_id: str) -> bool:
        segment = await self.get_segment(segment_id)
        if not segment:
            return False
        await self.db.delete(segment)
        await self.db.commit()
        return True

    async def assign_customers(self, segment_id: str, customer_ids: list[str]) -> int:
        count = 0
        for cid in customer_ids:
            existing = await self.db.execute(
                select(CustomerSegment).where(
                    CustomerSegment.segment_id == segment_id,
                    CustomerSegment.customer_id == cid,
                )
            )
            if not existing.scalar_one_or_none():
                self.db.add(CustomerSegment(segment_id=segment_id, customer_id=cid))
                count += 1
        await self.db.commit()
        return count

    async def remove_customer(self, segment_id: str, customer_id: str) -> bool:
        result = await self.db.execute(
            select(CustomerSegment).where(
                CustomerSegment.segment_id == segment_id,
                CustomerSegment.customer_id == customer_id,
            )
        )
        cs = result.scalar_one_or_none()
        if not cs:
            return False
        await self.db.delete(cs)
        await self.db.commit()
        return True

    async def get_segment_customers(self, segment_id: str) -> list[Customer]:
        result = await self.db.execute(
            select(Customer)
            .join(CustomerSegment, CustomerSegment.customer_id == Customer.id)
            .where(CustomerSegment.segment_id == segment_id)
        )
        return result.scalars().all()

    async def refresh_dynamic_segments(self, business_id: str) -> int:
        result = await self.db.execute(
            select(Segment).where(Segment.business_id == business_id, Segment.is_dynamic == True)
        )
        segments = result.scalars().all()
        refreshed = 0
        for seg in segments:
            if seg.rules:
                count = await self._compute_segment_count(business_id, seg.rules, seg.rule_operator)
                seg.customer_count = count
                seg.last_refreshed_at = datetime.now(timezone.utc)
                refreshed += 1
        await self.db.commit()
        return refreshed

    async def _compute_segment_count(self, business_id: str, rules: list, operator: str = "and") -> int:
        query = select(func.count(Customer.id)).where(Customer.business_id == business_id)
        conditions = []
        for rule in rules:
            field = rule.get("field", "")
            op = rule.get("op", "eq")
            value = rule.get("value")
            if field == "total_spent":
                sub = select(func.sum(Transaction.amount)).where(Transaction.business_id == business_id, Transaction.customer_id == Customer.id)
                if op == "gte":
                    conditions.append(sub.scalar_subquery() >= value)
                elif op == "lte":
                    conditions.append(sub.scalar_subquery() <= value)
                elif op == "gt":
                    conditions.append(sub.scalar_subquery() > value)
                elif op == "lt":
                    conditions.append(sub.scalar_subquery() < value)
            elif field == "total_orders":
                sub = select(func.count(Order.id)).where(Order.business_id == business_id, Order.customer_id == Customer.id)
                if op == "gte":
                    conditions.append(sub.scalar_subquery() >= value)
                elif op == "lte":
                    conditions.append(sub.scalar_subquery() <= value)
            elif field == "lifecycle_stage":
                if op == "eq":
                    conditions.append(Customer.lifecycle_stage == value)
                elif op == "in":
                    conditions.append(Customer.lifecycle_stage.in_(value))
            elif field == "tags":
                if op == "contains":
                    conditions.append(Customer.tags.contains([value]))
        if conditions:
            if operator == "and":
                query = query.where(and_(*conditions))
            else:
                query = query.where(or_(*conditions))
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_auto_segments(self, business_id: str) -> list[dict]:
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)
        segments = []
        high_value = await self.db.execute(
            select(func.count(Customer.id)).where(
                Customer.business_id == business_id,
                Customer.total_spent >= 5000,
            )
        )
        segments.append({"name": "High Value (>= ₹5000)", "count": high_value.scalar() or 0, "type": "auto"})
        active = await self.db.execute(
            select(func.count(Customer.id)).where(
                Customer.business_id == business_id,
                Customer.last_active >= thirty_days_ago,
            )
        )
        segments.append({"name": "Active (30d)", "count": active.scalar() or 0, "type": "auto"})
        new = await self.db.execute(
            select(func.count(Customer.id)).where(
                Customer.business_id == business_id,
                Customer.lifecycle_stage == "lead",
            )
        )
        segments.append({"name": "New Leads", "count": new.scalar() or 0, "type": "auto"})
        return segments
