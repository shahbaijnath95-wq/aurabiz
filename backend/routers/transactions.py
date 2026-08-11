from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from auth import get_current_user, verify_business_access
from models import User, Business, Transaction, Customer
from schemas import TransactionCreate, TransactionUpdate, TransactionResponse, TransactionSummary, SuccessResponse
from services.loyalty_manager import LoyaltyManager
from services.analytics_engine import AnalyticsEngine
from database import redis_client
from datetime import datetime

router = APIRouter(prefix="/api/v1/transactions", tags=["Transactions"])


@router.post("/record")
async def record_transaction(
    data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    business_result = await db.execute(select(Business).where(Business.user_id == current_user.id))
    business = business_result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business nahi mila")

    transaction = Transaction(
        business_id=business.id,
        customer_id=data.customer_id,
        amount=data.amount,
        currency=data.currency,
        type=data.type,
        status=data.status,
        items=data.items,
        payment_method=data.payment_method,
        reference=data.reference,
        notes=data.notes,
    )
    db.add(transaction)
    await db.flush()

    loyalty_earned = {}
    if data.customer_id and data.type == "sale" and data.status == "completed":
        lm = LoyaltyManager(db)
        loyalty_earned = await lm.earn_points(data.customer_id, data.amount, transaction.id)

    return {
        "status": "recorded",
        "transaction_id": transaction.id,
        "loyalty_earned": loyalty_earned,
    }


@router.get("/{business_id}")
async def list_transactions(
    business_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    type: str = Query(None),
    customer_id: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    query = select(Transaction).where(Transaction.business_id == business_id)
    if status:
        query = query.where(Transaction.status == status)
    if type:
        query = query.where(Transaction.type == type)
    if customer_id:
        query = query.where(Transaction.customer_id == customer_id)
    query = query.order_by(Transaction.created_at.desc()).offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    transactions = result.scalars().all()

    return {
        "transactions": [
            {
                "id": t.id, "amount": t.amount, "currency": t.currency,
                "type": t.type, "status": t.status, "payment_method": t.payment_method,
                "created_at": str(t.created_at) if t.created_at else None,
            }
            for t in transactions
        ],
        "page": page,
        "limit": limit,
    }


@router.get("/summary/{business_id}")
async def get_summary(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    from sqlalchemy import func
    result = await db.execute(
        select(
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
            func.avg(Transaction.amount).label("average"),
        ).where(Transaction.business_id == business_id, Transaction.status == "completed")
    )
    row = result.one_or_none()

    status_result = await db.execute(
        select(Transaction.status, func.count(Transaction.id))
        .where(Transaction.business_id == business_id)
        .group_by(Transaction.status)
    )
    by_status = {r[0]: r[1] for r in status_result.all()}

    return {
        "total": float(row[0]) if row and row[0] else 0,
        "count": row[1] if row else 0,
        "average": float(row[2]) if row and row[2] else 0,
        "by_status": by_status,
    }


@router.post("/bulk")
async def bulk_import(
    transactions: list[TransactionCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    for data in transactions:
        if not await verify_business_access(current_user, data.business_id, db):
            raise HTTPException(status_code=403, detail="Access denied")
    count = 0
    for data in transactions:
        t = Transaction(
            business_id=data.business_id, customer_id=data.customer_id,
            amount=data.amount, currency=data.currency, type=data.type,
            status=data.status, items=data.items,
        )
        db.add(t)
        count += 1
    await db.flush()
    return {"imported": count}


@router.get("/detail/{id}")
async def get_transaction(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Transaction).where(Transaction.id == id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Transaction nahi mili")
    if not await verify_business_access(current_user, t.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    return {
        "id": t.id, "amount": t.amount, "currency": t.currency,
        "type": t.type, "status": t.status, "items": t.items,
        "payment_method": t.payment_method, "notes": t.notes,
        "created_at": str(t.created_at) if t.created_at else None,
    }


@router.put("/{id}")
async def update_transaction(
    id: str,
    data: TransactionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Transaction).where(Transaction.id == id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Transaction nahi mili")
    if not await verify_business_access(current_user, t.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    if data.status:
        t.status = data.status
    if data.notes:
        t.notes = data.notes
    if data.payment_method:
        t.payment_method = data.payment_method
    await db.flush()
    return {"status": "updated", "transaction_id": t.id}
