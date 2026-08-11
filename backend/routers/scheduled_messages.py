"""
Scheduled Messages Router — Schedule WhatsApp messages, CRUD, status management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from database import get_db
from auth import get_current_user, verify_business_access
from models import ScheduledMessage, User
from services.scheduled_message_service import ScheduledMessageService
from schemas import ScheduledMessageCreate, ScheduledMessageUpdate, ScheduledMessageResponse

router = APIRouter(prefix="/api/v1/scheduled-messages", tags=["Scheduled Messages"])


async def _get_message_or_403(message_id: str, current_user: User, db: AsyncSession) -> ScheduledMessage:
    """Fetch a message and verify the user owns its business (prevents IDOR)."""
    svc = ScheduledMessageService(db)
    msg = await svc.get_message(message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message nahi mila")
    if not await verify_business_access(current_user, msg.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    return msg


@router.get("/{business_id}")
async def list_messages(business_id: str, status: str = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = ScheduledMessageService(db)
    msgs = await svc.list_messages(business_id, status)
    return {"messages": [{"id": m.id, "business_id": m.business_id, "customer_id": m.customer_id,
                           "content": m.content, "message_type": m.message_type,
                           "status": m.status, "scheduled_for": str(m.scheduled_for) if m.scheduled_for else None,
                           "sent_at": str(m.sent_at) if m.sent_at else None,
                           "created_at": str(m.created_at) if m.created_at else None} for m in msgs]}


@router.post("")
async def create_message(data: ScheduledMessageCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, data.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = ScheduledMessageService(db)
    msg = await svc.create_message(data.business_id, data.content, data.customer_id,
                                   data.message_type, data.template_name,
                                   data.template_vars, data.scheduled_for)
    return {"id": msg.id, "message": "Message schedule ho gaya!", "status": msg.status}


@router.get("/detail/{message_id}")
async def get_message(message_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    msg = await _get_message_or_403(message_id, current_user, db)
    return {"id": msg.id, "content": msg.content, "status": msg.status,
            "scheduled_for": str(msg.scheduled_for) if msg.scheduled_for else None}


@router.put("/{message_id}")
async def update_message(message_id: str, data: ScheduledMessageUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    msg = await _get_message_or_403(message_id, current_user, db)
    svc = ScheduledMessageService(db)
    msg = await svc.update_message(message_id, **data.model_dump(exclude_unset=True))
    if not msg:
        raise HTTPException(status_code=404, detail="Message nahi mila ya pending nahi hai")
    return {"message": "Message update ho gaya!"}


@router.post("/{message_id}/cancel")
async def cancel_message(message_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    msg = await _get_message_or_403(message_id, current_user, db)
    svc = ScheduledMessageService(db)
    msg = await svc.cancel_message(message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message nahi mila ya pending nahi hai")
    return {"message": "Message cancel ho gaya!"}


@router.delete("/{message_id}")
async def delete_message(message_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    msg = await _get_message_or_403(message_id, current_user, db)
    svc = ScheduledMessageService(db)
    ok = await svc.delete_message(message_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Message nahi mila")
    return {"message": "Message delete ho gaya!"}


@router.get("/pending/{business_id}")
async def pending_messages(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = ScheduledMessageService(db)
    msgs = await svc.get_pending_messages(business_id)
    return {"messages": [{"id": m.id, "content": m.content,
                           "scheduled_for": str(m.scheduled_for)} for m in msgs]}


@router.get("/stats/{business_id}")
async def message_stats(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = ScheduledMessageService(db)
    return await svc.get_message_stats(business_id)
