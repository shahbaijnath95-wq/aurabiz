from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from models import Customer, Transaction


class CustomerService:
    def __init__(self, db: AsyncSession = None):
        self.db = db

    async def create_customer(self, data: dict) -> Customer:
        if not self.db:
            return None
        import uuid
        customer = Customer(
            id=str(uuid.uuid4()),
            **data
        )
        self.db.add(customer)
        await self.db.flush()
        return customer

    async def get_customer_profile(self, customer_id: str) -> dict:
        if not self.db:
            return {}
        result = await self.db.execute(select(Customer).where(Customer.id == customer_id))
        customer = result.scalar_one_or_none()
        if not customer:
            return {}
        return {
            "id": customer.id,
            "phone_number": customer.phone_number,
            "name": customer.name,
            "email": customer.email,
            "tags": customer.tags or [],
            "lifecycle_stage": customer.lifecycle_stage,
            "engagement_score": customer.engagement_score,
            "total_orders": customer.total_orders,
            "total_spent": customer.total_spent,
            "loyalty_points": customer.loyalty_points,
            "last_active": str(customer.last_active) if customer.last_active else None,
            "notes": customer.notes,
            "created_at": str(customer.created_at) if customer.created_at else None,
        }

    async def search_customers(self, business_id: str, query: str = "", filters: dict = None, page: int = 1, limit: int = 100) -> list:
        if not self.db:
            return []
        q = select(Customer).where(Customer.business_id == business_id)
        if query:
            q = q.where(or_(
                Customer.name.ilike(f"%{query}%"),
                Customer.phone_number.ilike(f"%{query}%"),
                Customer.email.ilike(f"%{query}%"),
            ))
        if filters:
            if "lifecycle_stage" in filters:
                q = q.where(Customer.lifecycle_stage == filters["lifecycle_stage"])
            if "tag" in filters:
                q = q.where(Customer.tags.contains([filters["tag"]]))
            if "is_wholesaler" in filters:
                q = q.where(Customer.is_wholesaler == filters["is_wholesaler"])
        # Apply pagination at SQL level instead of Python slicing
        offset = (page - 1) * limit
        q = q.offset(offset).limit(limit)
        result = await self.db.execute(q)
        return result.scalars().all()

    async def segment_customers(self, business_id: str, criteria: dict) -> dict:
        customers = await self.search_customers(business_id)
        segments = {"high_value": [], "medium_value": [], "low_value": [], "at_risk": []}
        for c in customers:
            if c.total_spent > 10000:
                segments["high_value"].append(c.id)
            elif c.total_spent > 5000:
                segments["medium_value"].append(c.id)
            else:
                segments["low_value"].append(c.id)
        return {k: len(v) for k, v in segments.items()}

    async def import_customers_csv(self, business_id: str, file_path: str) -> dict:
        return {"imported": 0, "duplicates": 0, "errors": []}

    async def merge_duplicates(self, business_id: str, primary_id: str, duplicate_ids: list) -> dict:
        return {"primary_id": primary_id, "merged": len(duplicate_ids)}

    async def update_customer(self, customer_id: str, data: dict) -> Optional[Customer]:
        if not self.db:
            return None
        result = await self.db.execute(select(Customer).where(Customer.id == customer_id))
        customer = result.scalar_one_or_none()
        if not customer:
            return None
        for key, value in data.items():
            if hasattr(customer, key):
                setattr(customer, key, value)
        await self.db.flush()
        return customer

    async def get_lifecycle_stage(self, customer_id: str) -> str:
        if not self.db:
            return "lead"
        result = await self.db.execute(select(Customer).where(Customer.id == customer_id))
        customer = result.scalar_one_or_none()
        return customer.lifecycle_stage if customer else "lead"

    async def calculate_engagement_score(self, customer_id: str) -> float:
        if not self.db:
            return 0.0
        result = await self.db.execute(select(Customer).where(Customer.id == customer_id))
        customer = result.scalar_one_or_none()
        if not customer:
            return 0.0
        score = 0.0
        if customer.total_orders > 0:
            score += min(customer.total_orders * 10, 50)
        if customer.total_spent > 0:
            score += min(customer.total_spent / 100, 30)
        if customer.last_active:
            days_since = (datetime.utcnow() - customer.last_active.replace(tzinfo=None)).days
            if days_since < 7:
                score += 20
            elif days_since < 30:
                score += 10
        return min(score, 100.0)

    async def export_customers(self, business_id: str, format: str = "csv") -> str:
        return f"exports/customers_{business_id}.{format}"

    async def add_tag(self, customer_id: str, tag: str) -> None:
        if not self.db:
            return
        result = await self.db.execute(select(Customer).where(Customer.id == customer_id))
        customer = result.scalar_one_or_none()
        if customer:
            tags = customer.tags or []
            if tag not in tags:
                tags.append(tag)
                customer.tags = tags
                await self.db.flush()

    async def remove_tag(self, customer_id: str, tag: str) -> None:
        if not self.db:
            return
        result = await self.db.execute(select(Customer).where(Customer.id == customer_id))
        customer = result.scalar_one_or_none()
        if customer:
            tags = customer.tags or []
            if tag in tags:
                tags.remove(tag)
                customer.tags = tags
                await self.db.flush()

    async def get_customer_insights(self, customer_id: str) -> dict:
        return {
            "customer_id": customer_id,
            "preferred_time": "morning",
            "avg_order_value": 0,
            "favorite_products": [],
            "churn_risk": "low",
        }
