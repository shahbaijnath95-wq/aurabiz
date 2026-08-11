from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from auth import get_current_user, verify_business_access
from models import Customer, User
from schemas import LoyaltyProgramCreate, LoyaltyRedeem, LoyaltyEarn, SuccessResponse
from services.loyalty_manager import LoyaltyManager


async def _get_customer_or_403(customer_id: str, current_user: User, db: AsyncSession) -> Customer:
    """Fetch a customer and verify the user owns their business (prevents IDOR)."""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    cust = result.scalar_one_or_none()
    if not cust:
        raise HTTPException(status_code=404, detail="Customer nahi mila")
    if not await verify_business_access(current_user, cust.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    return cust

router = APIRouter(prefix="/api/v1/loyalty", tags=["Loyalty"])


@router.post("/programs")
async def create_program(
    data: LoyaltyProgramCreate,
    business_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    lm = LoyaltyManager(db)
    program = await lm.create_program(business_id, data.model_dump())
    return {"status": "created", "program_id": program.id}


@router.get("/programs")
async def list_programs(
    business_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    from sqlalchemy import select
    from models import LoyaltyProgram
    result = await db.execute(select(LoyaltyProgram).where(LoyaltyProgram.business_id == business_id))
    programs = result.scalars().all()
    return {"programs": [{"id": p.id, "name": p.name, "type": p.type, "is_active": p.is_active} for p in programs]}


@router.put("/programs/{id}")
async def update_program(
    id: str,
    data: LoyaltyProgramCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from models import LoyaltyProgram
    from sqlalchemy import select
    result = await db.execute(select(LoyaltyProgram).where(LoyaltyProgram.id == id))
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=404, detail="Program nahi mila")
    if not await verify_business_access(current_user, program.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    payload = data.model_dump(exclude_unset=True)
    for key, value in payload.items():
        if hasattr(program, key):
            setattr(program, key, value)
    await db.flush()
    return {"status": "updated", "program_id": id}


@router.get("/analytics/{business_id}")
async def get_analytics(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    lm = LoyaltyManager(db)
    return await lm.get_program_analytics(business_id)


@router.get("/tiers/{business_id}")
async def get_tiers(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    return {
        "tiers": [
            {"name": "Bronze", "min_points": 0, "max_points": 999},
            {"name": "Silver", "min_points": 1000, "max_points": 4999},
            {"name": "Gold", "min_points": 5000, "max_points": 19999},
            {"name": "Platinum", "min_points": 20000, "max_points": None},
        ]
    }


@router.post("/tiers")
async def create_tier(
    business_id: str = Query(...),
    tier_data: dict = {},
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    return {"status": "created", "tier": tier_data}


@router.get("/analytics/{business_id}/customer-segments")
async def get_segments(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    lm = LoyaltyManager(db)
    return {"segments": await lm.get_customer_segments(business_id)}


@router.post("/notifications")
async def send_notification(
    customer_id: str = Query(...),
    template: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cust = await _get_customer_or_403(customer_id, current_user, db)
    lm = LoyaltyManager(db)
    await lm.send_loyalty_notification(customer_id, template)
    return {"status": "sent"}


@router.post("/referrals")
async def create_referral(
    business_id: str = Query(...),
    reward_amount: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    lm = LoyaltyManager(db)
    return {"status": "created", "business_id": business_id}


@router.post("/referrals/track")
async def track_referral(
    referral_code: str,
    new_customer_phone: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lm = LoyaltyManager(db)
    return await lm.process_referral(referral_code, "")


@router.get("/balance/{customer_id}")
async def get_balance(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cust = await _get_customer_or_403(customer_id, current_user, db)
    lm = LoyaltyManager(db)
    balance = await lm.get_balance(customer_id)
    tier = await lm.get_tier(customer_id)
    return {"customer_id": customer_id, "balance": balance, "tier": tier}


@router.post("/redeem")
async def redeem(
    data: LoyaltyRedeem,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cust = await _get_customer_or_403(data.customer_id, current_user, db)
    lm = LoyaltyManager(db)
    return await lm.redeem_points(data.customer_id, data.points, data.reward_id)


@router.get("/history/{customer_id}")
async def get_history(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cust = await _get_customer_or_403(customer_id, current_user, db)
    from sqlalchemy import select
    from models import LoyaltyPoints
    result = await db.execute(
        select(LoyaltyPoints).where(LoyaltyPoints.customer_id == customer_id).order_by(LoyaltyPoints.created_at.desc())
    )
    records = result.scalars().all()
    return {"history": [{"id": r.id, "points": r.points, "balance": r.balance, "type": r.type, "created_at": str(r.created_at)} for r in records]}


@router.post("/earn")
async def earn(
    data: LoyaltyEarn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cust = await _get_customer_or_403(data.customer_id, current_user, db)
    lm = LoyaltyManager(db)
    return await lm.earn_points(data.customer_id, data.amount, data.transaction_id)
