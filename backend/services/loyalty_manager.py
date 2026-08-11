from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models import Transaction, Customer, Business


class LoyaltyManager:
    def __init__(self, db: AsyncSession = None):
        self.db = db

    async def create_program(self, business_id: str, config: dict) -> dict:
        from models import LoyaltyProgram
        program = LoyaltyProgram(business_id=business_id, **config)
        self.db.add(program)
        await self.db.flush()
        return program

    async def earn_points(self, customer_id: str, amount: float, transaction_id: str = None) -> dict:
        from models import LoyaltyPoints
        result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            return {"error": "Customer nahi mila"}

        points = int(amount)
        customer.loyalty_points += points
        customer.total_spent += amount
        customer.total_orders += 1

        loyalty_record = LoyaltyPoints(
            business_id=customer.business_id,
            customer_id=customer_id,
            points=points,
            balance=customer.loyalty_points,
            type="earn",
            reference_id=transaction_id,
            notes=f"₹{amount} purchase par {points} points mile",
        )
        self.db.add(loyalty_record)
        await self.db.flush()

        tier = await self.check_and_update_tier(customer_id)
        return {
            "points_earned": points,
            "total_balance": customer.loyalty_points,
            "tier": tier,
        }

    async def redeem_points(self, customer_id: str, points: int, reward_id: str = None) -> dict:
        from models import LoyaltyPoints
        result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            return {"error": "Customer nahi mila"}
        if customer.loyalty_points < points:
            return {"error": "Insufficient points"}

        customer.loyalty_points -= points
        loyalty_record = LoyaltyPoints(
            business_id=customer.business_id,
            customer_id=customer_id,
            points=-points,
            balance=customer.loyalty_points,
            type="redeem",
            reference_id=reward_id,
            notes=f"{points} points redeem kiye",
        )
        self.db.add(loyalty_record)
        await self.db.flush()
        return {"points_redeemed": points, "remaining_balance": customer.loyalty_points}

    async def get_balance(self, customer_id: str) -> int:
        result = await self.db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        return customer.loyalty_points if customer else 0

    async def get_tier(self, customer_id: str) -> str:
        balance = await self.get_balance(customer_id)
        if balance >= 20000:
            return "platinum"
        elif balance >= 5000:
            return "gold"
        elif balance >= 1000:
            return "silver"
        return "bronze"

    async def check_and_update_tier(self, customer_id: str) -> str:
        return await self.get_tier(customer_id)

    async def get_program_analytics(self, business_id: str) -> dict:
        from models import LoyaltyPoints
        result = await self.db.execute(
            select(func.count(LoyaltyPoints.id), func.sum(LoyaltyPoints.points))
            .where(LoyaltyPoints.business_id == business_id)
        )
        row = result.one_or_none()
        return {
            "total_members": row[0] if row else 0,
            "total_points_issued": row[1] if row and row[1] else 0,
            "active_members": 0,
            "redemption_rate": 0.0,
        }

    async def create_reward(self, business_id: str, reward_config: dict) -> dict:
        return {"id": "reward-1", "business_id": business_id, **reward_config, "status": "active"}

    async def get_available_rewards(self, business_id: str) -> list:
        return []

    async def generate_referral_code(self, customer_id: str) -> str:
        import hashlib
        return hashlib.md5(customer_id.encode()).hexdigest()[:8].upper()

    async def process_referral(self, referral_code: str, new_customer_id: str) -> dict:
        return {"referral_code": referral_code, "new_customer_id": new_customer_id, "status": "processed"}

    async def get_referral_stats(self, business_id: str) -> dict:
        return {"total_referrals": 0, "successful_referrals": 0, "total_rewards_given": 0}

    async def send_loyalty_notification(self, customer_id: str, template: str) -> None:
        pass

    async def get_customer_segments(self, business_id: str) -> list:
        return [
            {"name": "High Value", "criteria": "total_spent > 10000", "count": 0},
            {"name": "Regular", "criteria": "total_orders > 5", "count": 0},
            {"name": "At Risk", "criteria": "last_active > 30 days", "count": 0},
        ]

    async def bulk_earn_points(self, customer_ids: list, points: int, reason: str = None) -> dict:
        results = []
        for cid in customer_ids:
            r = await self.earn_points(cid, points)
            results.append(r)
        return {"processed": len(results), "results": results}

    async def expiring_points_reminder(self) -> None:
        pass

    async def process_refund_points(self, transaction_id: str) -> None:
        pass
