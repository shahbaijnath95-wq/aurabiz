from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models import User, Business, Integration, APIKey, ScheduledMessage, Payment
from .payment_manager import PaymentManager


class AdminService:
    def __init__(self, db: AsyncSession = None):
        self.db = db

    async def get_user_management(self, page: int = 1, limit: int = 20) -> dict:
        if not self.db:
            return {"users": [], "total": 0}
        result = await self.db.execute(select(User).offset((page - 1) * limit).limit(limit))
        users = result.scalars().all()
        count_result = await self.db.execute(select(func.count(User.id)))
        total = count_result.scalar() or 0
        return {
            "users": [{"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role, "is_active": u.is_active} for u in users],
            "total": total,
            "page": page,
            "limit": limit,
        }

    async def update_user_role(self, user_id: str, role: str) -> Optional[User]:
        if not self.db:
            return None
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.role = role
            await self.db.flush()
        return user

    async def get_billing_overview(self) -> dict:
        return {"total_revenue": 0, "active_subscriptions": 0, "mrr": 0}

    async def update_subscription(self, user_id: str, tier: str) -> dict:
        return {"user_id": user_id, "tier": tier, "status": "updated"}

    async def check_subscription_status(self, user_id: str) -> dict:
        return {"user_id": user_id, "tier": "free", "status": "active", "expires_at": None}

    async def get_integration_health(self) -> dict:
        return {"integrations": [], "healthy": 0, "unhealthy": 0}

    async def force_reconnect(self, integration_type: str) -> bool:
        return True

    async def get_master_api_keys(self) -> list:
        if not self.db:
            return []
        result = await self.db.execute(select(APIKey))
        return result.scalars().all()

    async def create_master_api_key(self, name: str, permissions: list) -> APIKey:
        import uuid
        import hashlib
        key = f"sk_{uuid.uuid4().hex}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        api_key = APIKey(
            business_id="master",
            name=name,
            key_hash=key_hash,
            key_prefix=key[:10],
            permissions=permissions,
        )
        self.db.add(api_key)
        await self.db.flush()
        return api_key

    async def revoke_master_api_key(self, key_id: str) -> bool:
        if not self.db:
            return False
        result = await self.db.execute(select(APIKey).where(APIKey.id == key_id))
        key = result.scalar_one_or_none()
        if key:
            key.is_active = False
            await self.db.flush()
            return True
        return False

    async def get_notification_queue(self) -> list:
        if not self.db:
            return []
        result = await self.db.execute(
            select(ScheduledMessage).where(ScheduledMessage.status == "pending").limit(50)
        )
        return result.scalars().all()

    async def send_notification(self, user_id: str, notification_data: dict) -> bool:
        return True

    async def broadcast_notification(self, notification_data: dict) -> int:
        return 0

    async def get_payments(self, page: int = 1, limit: int = 20) -> dict:
        payment_manager = PaymentManager(self.db)
        return await payment_manager.get_payments(page, limit)

    async def update_payment_status(self, payment_id: str, status: str, updated_by: str) -> dict:
        payment_manager = PaymentManager(self.db)
        updated_payment = await payment_manager.update_payment_status(payment_id, status, updated_by)
        if updated_payment:
            return updated_payment.to_dict()
        return {"id": payment_id, "status": status, "updated_by": updated_by, "updated_at": datetime.now().isoformat()}

    async def generate_payment_qr(self, amount: float, customer_name: str = None, customer_email: str = None, customer_phone: str = None, business_id: str = None) -> dict:
        payment_manager = PaymentManager(self.db)
        return await payment_manager.generate_qr_payment(
            business_id=business_id or "business-1",
            amount=amount,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone
        )

    async def get_latest_qr(self, business_id: str) -> dict:
        return {"business_id": business_id, "qr": None, "status": "qr_code_service_unavailable"}
