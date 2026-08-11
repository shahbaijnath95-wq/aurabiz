"""
Inventory Alerts Router — Low stock notifications, threshold config, alert management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from database import get_db
from auth import get_current_user, verify_business_access
from models import InventoryAlert, User
from services.inventory_alert_service import InventoryAlertService
from schemas import InventoryAlertCreate, InventoryAlertUpdate, InventoryAlertResponse

router = APIRouter(prefix="/api/v1/inventory-alerts", tags=["Inventory Alerts"])


async def _get_alert_or_403(alert_id: str, current_user: User, db: AsyncSession) -> InventoryAlert:
    """Fetch an alert and verify the user owns its business (prevents IDOR)."""
    result = await db.execute(select(InventoryAlert).where(InventoryAlert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert nahi mila")
    if not await verify_business_access(current_user, alert.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    return alert


@router.get("/{business_id}")
async def list_alerts(business_id: str, resolved: bool = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = InventoryAlertService(db)
    alerts = await svc.list_alerts(business_id, resolved)
    return {"alerts": [{"id": a.id, "business_id": a.business_id, "product_id": a.product_id,
                         "alert_type": a.alert_type, "threshold": a.threshold,
                         "current_stock": a.current_stock, "message": a.message,
                         "is_resolved": a.is_resolved,
                         "created_at": str(a.created_at) if a.created_at else None} for a in alerts]}


@router.post("")
async def create_alert(data: InventoryAlertCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, data.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = InventoryAlertService(db)
    alert = await svc.create_alert(data.business_id, data.product_id, data.alert_type,
                                   data.threshold, data.message, data.notified_channels)
    return {"id": alert.id, "message": "Alert ban gaya!", "alert_type": alert.alert_type}


@router.put("/{alert_id}")
async def update_alert(alert_id: str, data: InventoryAlertUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    alert = await _get_alert_or_403(alert_id, current_user, db)
    svc = InventoryAlertService(db)
    alert = await svc.update_alert(alert_id, **data.model_dump(exclude_unset=True))
    if not alert:
        raise HTTPException(status_code=404, detail="Alert nahi mila")
    return {"message": "Alert update ho gaya!"}


@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    alert = await _get_alert_or_403(alert_id, current_user, db)
    svc = InventoryAlertService(db)
    alert = await svc.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert nahi mila")
    return {"message": "Alert resolve ho gaya!"}


@router.delete("/{alert_id}")
async def delete_alert(alert_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    alert = await _get_alert_or_403(alert_id, current_user, db)
    svc = InventoryAlertService(db)
    ok = await svc.delete_alert(alert_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Alert nahi mila")
    return {"message": "Alert delete ho gaya!"}


@router.post("/check/{business_id}")
async def check_stock_alerts(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = InventoryAlertService(db)
    alerts = await svc.check_stock_alerts(business_id)
    return {"message": f"{len(alerts)} naye alerts bane!", "new_alerts": len(alerts)}


@router.get("/stats/{business_id}")
async def alert_stats(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = InventoryAlertService(db)
    return await svc.get_alert_stats(business_id)

