from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
import uuid

from database import get_db
from auth import get_current_user, verify_business_access
from models import User, Booking

router = APIRouter(prefix="/api/v1", tags=["Orders & Bookings"])


# ──────────── BOOKING ENDPOINTS ────────────

@router.get("/bookings/{business_id}")
async def list_bookings(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(
        select(Booking).where(Booking.business_id == business_id).order_by(desc(Booking.created_at)).limit(100)
    )
    bookings = result.scalars().all()
    return {
        "bookings": [
            {
                "id": b.id,
                "service_name": b.service_name,
                "customer_name": b.customer_name or "Customer",
                "customer_phone": b.customer_phone or "",
                "booking_date": b.booking_date,
                "booking_time": b.booking_time,
                "duration_minutes": b.duration_minutes or 30,
                "price": b.price or 0,
                "status": b.status,
                "notes": b.notes or "",
                "created_at": str(b.created_at) if b.created_at else None,
            }
            for b in bookings
        ]
    }


class BookingStatusUpdate(BaseModel):
    status: str


@router.put("/bookings/{booking_id}/status")
async def update_booking_status(booking_id: str, data: BookingStatusUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if not await verify_business_access(current_user, booking.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    booking.status = data.status
    await db.commit()
    return {"status": "updated", "booking_id": booking_id, "new_status": data.status}

