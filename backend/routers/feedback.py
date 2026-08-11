"""Customer feedback - ratings and reviews."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from database import get_db
from models import Feedback, Customer, User
from schemas import FeedbackCreate
from auth import get_current_user, verify_business_access

router = APIRouter(prefix="/api/v1", tags=["feedback"])


@router.post("/feedback")
async def submit_feedback(req: FeedbackCreate, db: AsyncSession = Depends(get_db)):
    feedback = Feedback(
        business_id=req.business_id,
        customer_id=req.customer_id,
        order_id=req.order_id,
        rating=req.rating,
        comment=req.comment,
    )
    db.add(feedback)
    await db.commit()
    return {"status": "submitted", "feedback_id": feedback.id}


@router.get("/feedback/{business_id}")
async def list_feedback(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(
        select(Feedback).where(Feedback.business_id == business_id).order_by(desc(Feedback.created_at)).limit(100)
    )
    feedbacks = result.scalars().all()
    items = []
    for f in feedbacks:
        cust_name = None
        if f.customer_id:
            cust_result = await db.execute(select(Customer).where(Customer.id == f.customer_id))
            cust = cust_result.scalar_one_or_none()
            cust_name = cust.name if cust else None
        items.append({
            "id": f.id, "customer_name": cust_name, "rating": f.rating,
            "comment": f.comment, "order_id": f.order_id,
            "created_at": str(f.created_at) if f.created_at else None,
        })
    return {"feedbacks": items}


@router.get("/feedback/{business_id}/stats")
async def feedback_stats(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(select(Feedback).where(Feedback.business_id == business_id))
    feedbacks = list(result.scalars().all())
    total = len(feedbacks)
    if total == 0:
        return {"total": 0, "average_rating": 0, "5_star": 0, "4_star": 0, "3_star": 0, "2_star": 0, "1_star": 0}
    avg = sum(f.rating for f in feedbacks) / total
    return {
        "total": total,
        "average_rating": round(avg, 1),
        "5_star": sum(1 for f in feedbacks if f.rating == 5),
        "4_star": sum(1 for f in feedbacks if f.rating == 4),
        "3_star": sum(1 for f in feedbacks if f.rating == 3),
        "2_star": sum(1 for f in feedbacks if f.rating == 2),
        "1_star": sum(1 for f in feedbacks if f.rating == 1),
    }
