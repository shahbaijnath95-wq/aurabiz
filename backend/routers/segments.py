"""
Segments Router — Customer segment builder, auto-segment rules, behavioral segments.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from database import get_db
from auth import get_current_user, verify_business_access
from models import User
from services.segment_service import SegmentService
from schemas import SegmentCreate, SegmentUpdate, SegmentResponse, CustomerSegmentAssign

router = APIRouter(prefix="/api/v1/segments", tags=["Segments"])


@router.get("/{business_id}")
async def list_segments(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = SegmentService(db)
    segments = await svc.list_segments(business_id)
    return {"segments": [{"id": s.id, "business_id": s.business_id, "name": s.name,
                           "description": s.description, "rules": s.rules or [],
                           "rule_operator": s.rule_operator, "is_dynamic": s.is_dynamic,
                           "customer_count": s.customer_count,
                           "created_at": str(s.created_at) if s.created_at else None} for s in segments]}


@router.post("")
async def create_segment(data: SegmentCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, data.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = SegmentService(db)
    rules = [r.model_dump() for r in data.rules] if data.rules else []
    seg = await svc.create_segment(data.business_id, data.name, data.description,
                                   rules, data.rule_operator, data.is_dynamic)
    return {"id": seg.id, "name": seg.name, "customer_count": seg.customer_count,
            "message": "Segment ban gaya!"}


@router.get("/detail/{segment_id}")
async def get_segment(segment_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    svc = SegmentService(db)
    seg = await svc.get_segment(segment_id)
    if not seg:
        raise HTTPException(status_code=404, detail="Segment nahi mila")
    if not await verify_business_access(current_user, seg.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    customers = await svc.get_segment_customers(segment_id)
    return {
        "id": seg.id, "name": seg.name, "description": seg.description,
        "rules": seg.rules or [], "rule_operator": seg.rule_operator,
        "is_dynamic": seg.is_dynamic, "customer_count": seg.customer_count,
        "customers": [{"id": c.id, "phone": c.phone_number, "name": c.name} for c in customers],
    }


@router.put("/{segment_id}")
async def update_segment(segment_id: str, data: SegmentUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    svc = SegmentService(db)
    seg = await svc.get_segment(segment_id)
    if not seg:
        raise HTTPException(status_code=404, detail="Segment nahi mila")
    if not await verify_business_access(current_user, seg.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    update_data = data.model_dump(exclude_unset=True)
    if "rules" in update_data and update_data["rules"]:
        update_data["rules"] = [r.model_dump() for r in data.rules]
    seg = await svc.update_segment(segment_id, **update_data)
    if not seg:
        raise HTTPException(status_code=404, detail="Segment nahi mila")
    return {"message": "Segment update ho gaya!", "customer_count": seg.customer_count}


@router.delete("/{segment_id}")
async def delete_segment(segment_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    svc = SegmentService(db)
    seg = await svc.get_segment(segment_id)
    if not seg:
        raise HTTPException(status_code=404, detail="Segment nahi mila")
    if not await verify_business_access(current_user, seg.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    ok = await svc.delete_segment(segment_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Segment nahi mila")
    return {"message": "Segment delete ho gaya!"}


@router.post("/{segment_id}/assign")
async def assign_customers(segment_id: str, data: CustomerSegmentAssign, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    svc = SegmentService(db)
    seg = await svc.get_segment(segment_id)
    if not seg:
        raise HTTPException(status_code=404, detail="Segment nahi mila")
    if not await verify_business_access(current_user, seg.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    count = await svc.assign_customers(segment_id, data.customer_ids)
    return {"message": f"{count} customers assign ho gaye!", "assigned": count}


@router.delete("/{segment_id}/customers/{customer_id}")
async def remove_customer(segment_id: str, customer_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    svc = SegmentService(db)
    seg = await svc.get_segment(segment_id)
    if not seg:
        raise HTTPException(status_code=404, detail="Segment nahi mila")
    if not await verify_business_access(current_user, seg.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    ok = await svc.remove_customer(segment_id, customer_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Customer segment mein nahi tha")
    return {"message": "Customer remove ho gaya!"}


@router.post("/refresh/{business_id}")
async def refresh_segments(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = SegmentService(db)
    count = await svc.refresh_dynamic_segments(business_id)
    return {"message": f"{count} segments refresh ho gaye!", "refreshed": count}


@router.get("/auto/{business_id}")
async def auto_segments(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = SegmentService(db)
    return {"segments": await svc.get_auto_segments(business_id)}
