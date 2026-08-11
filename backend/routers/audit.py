from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from auth import get_current_user, verify_business_access
from models import User
from services.audit_service import AuditService

router = APIRouter(prefix="/api/v1/audit", tags=["Audit"])


@router.get("/{business_id}")
async def get_audit_logs(
    business_id: str,
    action: str = Query(None),
    entity_type: str = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    service = AuditService(db)
    filters = {"limit": limit}
    if action:
        filters["action"] = action
    if entity_type:
        filters["entity_type"] = entity_type
    logs = await service.get_audit_logs(business_id, filters)
    return {
        "logs": [
            {
                "id": l.id, "action": l.action, "entity_type": l.entity_type,
                "entity_id": l.entity_id, "changes": l.changes,
                "ip_address": l.ip_address, "timestamp": str(l.timestamp) if l.timestamp else None,
            }
            for l in logs
        ]
    }


@router.get("/compliance/{business_id}")
async def compliance_report(
    business_id: str,
    period: str = Query("30d"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    service = AuditService(db)
    return await service.get_compliance_report(business_id, period)


@router.get("/export/{business_id}")
async def export_logs(
    business_id: str,
    format: str = Query("csv"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    service = AuditService(db)
    path = await service.export_audit_logs(business_id, format)
    return {"file_path": path, "format": format}
