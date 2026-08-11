"""
Follow-Ups Router — Automated follow-up rules, scheduling, status management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from database import get_db
from auth import get_current_user, verify_business_access
from models import FollowUp, User
from services.followup_service import FollowUpService
from schemas import FollowUpCreate, FollowUpUpdate, FollowUpResponse

router = APIRouter(prefix="/api/v1/followups", tags=["Follow-Ups"])


async def _get_followup_or_403(followup_id: str, current_user: User, db: AsyncSession) -> FollowUp:
    """Fetch a follow-up and verify the user owns its business (prevents IDOR)."""
    result = await db.execute(select(FollowUp).where(FollowUp.id == followup_id))
    fu = result.scalar_one_or_none()
    if not fu:
        raise HTTPException(status_code=404, detail="Follow-up nahi mila")
    if not await verify_business_access(current_user, fu.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    return fu


@router.get("/stats/{business_id}")
async def followup_stats(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = FollowUpService(db)
    return await svc.get_followup_stats(business_id)


@router.get("/pending/{business_id}")
async def pending_followups(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = FollowUpService(db)
    msgs = await svc.get_pending_followups(business_id)
    return {"followups": [{"id": f.id, "customer_id": f.customer_id,
                            "message_template": f.message_template,
                            "status": f.status, "scheduled_for": str(f.scheduled_for)} for f in msgs]}


@router.get("/{business_id}")
async def list_followups(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = FollowUpService(db)
    followups = await svc.list_followups(business_id)
    return {"followups": [{"id": f.id, "business_id": f.business_id, "customer_id": f.customer_id,
                            "message_template": f.message_template, "status": f.status,
                            "scheduled_for": str(f.scheduled_for) if f.scheduled_for else None} for f in followups]}


@router.post("")
async def create_followup(data: FollowUpCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, data.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = FollowUpService(db)
    fu = await svc.create_followup(data.business_id, data.message_template, data.customer_id,
                                   data.trigger_type, data.trigger_reference_id, data.delay_hours)
    return {"id": fu.id, "message": "Follow-up ban gaya!", "status": fu.status}


@router.put("/{followup_id}")
async def update_followup(followup_id: str, data: FollowUpUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    fu = await _get_followup_or_403(followup_id, current_user, db)
    svc = FollowUpService(db)
    fu = await svc.update_followup(followup_id, **data.model_dump(exclude_unset=True))
    if not fu:
        raise HTTPException(status_code=404, detail="Follow-up nahi mila")
    return {"message": "Follow-up update ho gaya!"}


@router.post("/{followup_id}/cancel")
async def cancel_followup(followup_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    fu = await _get_followup_or_403(followup_id, current_user, db)
    svc = FollowUpService(db)
    fu = await svc.cancel_followup(followup_id)
    if not fu:
        raise HTTPException(status_code=404, detail="Follow-up nahi mila")
    return {"message": "Follow-up cancel ho gaya!"}


@router.post("/{followup_id}/send")
async def send_followup(followup_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    fu = await _get_followup_or_403(followup_id, current_user, db)
    svc = FollowUpService(db)
    fu = await svc.mark_sent(followup_id)
    if not fu:
        raise HTTPException(status_code=404, detail="Follow-up nahi mila")
    return {"message": "Follow-up bhej diya!"}


@router.post("/{followup_id}/fail")
async def fail_followup(followup_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    fu = await _get_followup_or_403(followup_id, current_user, db)
    svc = FollowUpService(db)
    fu = await svc.mark_failed(followup_id, "manual_fail")
    if not fu:
        raise HTTPException(status_code=404, detail="Follow-up nahi mila")
    return {"message": "Follow-up fail mark ho gaya!"}


@router.delete("/{followup_id}")
async def delete_followup(followup_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    fu = await _get_followup_or_403(followup_id, current_user, db)
    svc = FollowUpService(db)
    ok = await svc.delete_followup(followup_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Follow-up nahi mila")
    return {"message": "Follow-up delete ho gaya!"}


@router.post("/auto/order")
async def auto_create_order_followup(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, data.get("business_id", ""), db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = FollowUpService(db)
    fu = await svc.auto_create_order_followup(
        data.get("business_id", ""), data.get("customer_id", ""),
        data.get("order_id", ""), data.get("product_name", ""))
    return {"id": fu.id, "message": "Order follow-up schedule ho gaya!"}


@router.post("/auto/appointment")
async def auto_create_appointment_followup(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, data.get("business_id", ""), db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = FollowUpService(db)
    fu = await svc.auto_create_appointment_followup(
        data.get("business_id", ""), data.get("customer_id", ""),
        data.get("booking_id", ""), data.get("service_name", ""))
    return {"id": fu.id, "message": "Appointment follow-up schedule ho gaya!"}
