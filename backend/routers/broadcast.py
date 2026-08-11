"""Broadcast messages - send messages to all customers."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database import get_db
from models import Broadcast, Customer, WhatsAppMessage, User
from schemas import BroadcastCreate
from auth import get_current_user, verify_business_access

router = APIRouter(prefix="/api/v1", tags=["broadcast"])


@router.post("/broadcast")
async def create_broadcast(req: BroadcastCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, req.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    cust_result = await db.execute(
        select(Customer).where(Customer.business_id == req.business_id)
    )
    customers = list(cust_result.scalars().all())

    broadcast = Broadcast(
        business_id=req.business_id,
        message=req.message,
        target_count=len(customers),
        status="pending",
    )
    db.add(broadcast)
    await db.flush()

    sent_count = 0
    failed_count = 0
    for cust in customers:
        try:
            msg = WhatsAppMessage(
                business_id=req.business_id,
                customer_id=cust.id,
                direction="outbound",
                content=req.message,
                message_type="text",
                status="sent",
            )
            db.add(msg)
            sent_count += 1
        except Exception:
            failed_count += 1

    broadcast.sent_count = sent_count
    broadcast.failed_count = failed_count
    broadcast.status = "sent"
    await db.commit()

    return {
        "status": "sent",
        "broadcast_id": broadcast.id,
        "target_count": len(customers),
        "sent_count": sent_count,
        "failed_count": failed_count,
    }


@router.get("/broadcast/{business_id}")
async def list_broadcasts(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(
        select(Broadcast).where(Broadcast.business_id == business_id).order_by(desc(Broadcast.created_at)).limit(50)
    )
    broadcasts = result.scalars().all()
    return {"broadcasts": [
        {
            "id": b.id, "message": b.message, "target_count": b.target_count,
            "sent_count": b.sent_count, "failed_count": b.failed_count,
            "status": b.status,
            "created_at": str(b.created_at) if b.created_at else None,
        }
        for b in broadcasts
    ]}
