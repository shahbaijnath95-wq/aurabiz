from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import AuditLog
import uuid
import json


class AuditService:
    def __init__(self, db: AsyncSession = None):
        self.db = db

    async def log_action(
        self, business_id: str, action: str, entity_type: str,
        entity_id: str = None, changes: dict = None,
        ip_address: str = None, user_agent: str = None,
    ) -> AuditLog:
        log = AuditLog(
            business_id=business_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=changes or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def get_audit_logs(self, business_id: str, filters: dict = None) -> list:
        query = select(AuditLog).where(AuditLog.business_id == business_id)
        if filters:
            if "action" in filters:
                query = query.where(AuditLog.action == filters["action"])
            if "entity_type" in filters:
                query = query.where(AuditLog.entity_type == filters["entity_type"])
        query = query.order_by(AuditLog.timestamp.desc()).limit(filters.get("limit", 100) if filters else 100)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def export_audit_logs(self, business_id: str, format: str = "csv") -> str:
        return f"exports/audit_{business_id}.{format}"

    async def get_compliance_report(self, business_id: str, period: str = "30d") -> dict:
        return {
            "business_id": business_id,
            "period": period,
            "total_actions": 0,
            "data_access_events": 0,
            "permission_changes": 0,
            "security_events": 0,
            "status": "compliant",
        }
