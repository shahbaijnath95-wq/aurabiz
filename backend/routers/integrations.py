from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from auth import get_current_user, verify_business_access
from models import User, Business, Integration
from schemas import IntegrationConnect, SuccessResponse
from services.google_business import GoogleBusinessService
from services.instagram_service import InstagramService
from services.razorpay_client import RazorpayClient
from services.phonepe_client import PhonePeClient
from services.tally_client import TallyClient

router = APIRouter(prefix="/api/v1/integrations", tags=["Integrations"])


@router.post("/connect/google-business")
async def connect_google_business(
    data: IntegrationConnect,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, data.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await GoogleBusinessService().connect(data.business_id, data.credentials)
    integration = Integration(business_id=data.business_id, type="google_business", status="connected", config=data.config, credentials=data.credentials)
    db.add(integration)
    await db.flush()
    return result


@router.post("/connect/instagram")
async def connect_instagram(
    data: IntegrationConnect,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, data.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await InstagramService().connect(data.business_id, data.credentials)
    integration = Integration(business_id=data.business_id, type="instagram", status="connected", config=data.config, credentials=data.credentials)
    db.add(integration)
    await db.flush()
    return result


@router.post("/connect/phonepe")
async def connect_phonepe(
    data: IntegrationConnect,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, data.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await PhonePeClient().connect(data.business_id, data.credentials)
    integration = Integration(business_id=data.business_id, type="phonepe", status="connected", config=data.config, credentials=data.credentials)
    db.add(integration)
    await db.flush()
    return result


@router.post("/connect/tally")
async def connect_tally(
    data: IntegrationConnect,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, data.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await TallyClient().connect(data.business_id, data.credentials)
    integration = Integration(business_id=data.business_id, type="tally", status="connected", config=data.config, credentials=data.credentials)
    db.add(integration)
    await db.flush()
    return result


@router.post("/connect/razorpay")
async def connect_razorpay(
    data: IntegrationConnect,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, data.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await RazorpayClient().connect(data.business_id, data.credentials)
    integration = Integration(business_id=data.business_id, type="razorpay", status="connected", config=data.config, credentials=data.credentials)
    db.add(integration)
    await db.flush()
    return result


@router.get("/status/{business_id}")
async def get_status(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(select(Integration).where(Integration.business_id == business_id))
    integrations = result.scalars().all()
    return {"integrations": [{"type": i.type, "status": i.status, "last_synced": str(i.last_synced_at) if i.last_synced_at else None} for i in integrations]}


@router.post("/disconnect/{type}")
async def disconnect(
    type: str,
    business_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    result = await db.execute(select(Integration).where(Integration.business_id == business_id, Integration.type == type))
    integration = result.scalar_one_or_none()
    if integration:
        integration.status = "disconnected"
        await db.flush()
    return {"status": "disconnected", "type": type}


@router.get("/reviews/{business_id}")
async def get_reviews(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    return await GoogleBusinessService().get_reviews(business_id)


@router.post("/google-business/reply/{review_id}")
async def reply_review(
    review_id: str,
    response_text: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await GoogleBusinessService().reply_to_review(review_id, response_text)


@router.get("/instagram/messages/{business_id}")
async def get_instagram_messages(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    return await InstagramService().get_messages(business_id)


@router.get("/instagram/media/{business_id}")
async def get_instagram_media(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    return await InstagramService().get_media(business_id)


@router.post("/tally/sync/{business_id}")
async def sync_tally(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    return await TallyClient().sync_transactions(business_id)


@router.get("/tally/reports/{business_id}")
async def tally_reports(
    business_id: str,
    report_type: str = Query("profit_loss"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    return await TallyClient().get_reports(business_id, report_type)


@router.post("/razorpay/create-payment-link")
async def create_razorpay_link(
    amount: float,
    description: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await RazorpayClient().create_payment_link(amount, description)


@router.get("/razorpay/transaction/{id}")
async def razorpay_status(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await RazorpayClient().get_payment(id)


@router.post("/phonepe/create-payment")
async def create_phonepe_payment(
    amount: float,
    business_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    return await PhonePeClient().create_payment(amount)


@router.get("/phonepe/status/{id}")
async def phonepe_status(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await PhonePeClient().check_status(id)
