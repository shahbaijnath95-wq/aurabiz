from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from auth import get_current_user, verify_business_access
from models import User
from services.revenue_forecaster import RevenueForecaster

router = APIRouter(prefix="/api/v1/revenue", tags=["Revenue Intelligence"])


@router.get("/forecast/{business_id}")
async def forecast(
    business_id: str,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    f = RevenueForecaster(db)
    return await f.forecast_revenue(business_id, days)


@router.get("/patterns/{business_id}")
async def patterns(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    f = RevenueForecaster(db)
    return await f.analyze_patterns(business_id)


@router.get("/alerts/{business_id}")
async def alerts(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    f = RevenueForecaster(db)
    return await f.generate_alerts(business_id)


@router.get("/what-if/{business_id}")
async def what_if(
    business_id: str,
    price_change: float = Query(0),
    volume_change: float = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    f = RevenueForecaster(db)
    return await f.run_what_if(business_id, [{"price_change": price_change, "volume_change": volume_change}])
