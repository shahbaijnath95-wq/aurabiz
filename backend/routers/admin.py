from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from auth import get_current_user, require_admin
from models import User
from schemas import AdminUserRoleUpdate, AdminSubscriptionUpdate, NotificationSend, BroadcastNotification, APIKeyCreate, SuccessResponse
from services.admin_service import AdminService

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    admin = AdminService(db)
    return await admin.get_user_management(page, limit)


@router.get("/users/{id}")
async def get_user(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User nahi mila")
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role, "is_active": user.is_active}


@router.put("/users/{id}/role")
async def update_role(
    id: str,
    data: AdminUserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    admin = AdminService(db)
    user = await admin.update_user_role(id, data.role)
    if not user:
        raise HTTPException(status_code=404, detail="User nahi mila")
    return {"status": "updated", "role": user.role}


@router.get("/billing/overview")
async def billing_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await AdminService(db).get_billing_overview()


@router.get("/billing/subscription/{user_id}")
async def get_subscription(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await AdminService(db).check_subscription_status(user_id)


@router.put("/billing/subscription/{user_id}")
async def update_subscription(
    user_id: str,
    data: AdminSubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await AdminService(db).update_subscription(user_id, data.tier)


@router.get("/integrations/overview")
async def integration_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await AdminService(db).get_integration_health()


@router.post("/integrations/{type}/reconnect")
async def reconnect(
    type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await AdminService(db).force_reconnect(type)


@router.get("/api-keys")
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    keys = await AdminService(db).get_master_api_keys()
    return {"api_keys": [{"id": k.id, "name": k.name, "key_prefix": k.key_prefix, "is_active": k.is_active} for k in keys]}


@router.post("/api-keys")
async def create_api_key(
    data: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    key = await AdminService(db).create_master_api_key(data.name, data.permissions)
    return {"status": "created", "key_id": key.id, "key_prefix": key.key_prefix}


@router.delete("/api-keys/{id}")
async def revoke_api_key(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await AdminService(db).revoke_master_api_key(id)
    return {"status": "revoked" if result else "not_found"}


@router.get("/payments")
async def list_payments(
    business_id: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await AdminService(db).get_payments(page, limit)


@router.post("/payments/{id}/status")
async def update_payment_status(
    id: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await AdminService(db).update_payment_status(id, data.status, current_user.id)


@router.post("/qr/generate")
async def generate_qr(
    amount: float = Query(..., ge=0),
    business_id: str = Query(None),
    customer_name: str = Query(None),
    customer_email: str = Query(None),
    customer_phone: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await AdminService(db).generate_payment_qr(amount, customer_name, customer_email, customer_phone, business_id=business_id)


@router.get("/qr/{business_id}")
async def get_qr(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await AdminService(db).get_latest_qr(business_id)


@router.get("/notifications/queue")
async def notification_queue(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    queue = await AdminService(db).get_notification_queue()
    return {"queue": [{"id": m.id, "content": m.content, "status": m.status, "scheduled_for": str(m.scheduled_for)} for m in queue]}


@router.post("/notifications/send")
async def send_notification(
    data: NotificationSend,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await AdminService(db).send_notification(data.user_id, {"title": data.title, "message": data.message, "channel": data.channel})


@router.post("/notifications/broadcast")
async def broadcast(
    data: BroadcastNotification,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    count = await AdminService(db).broadcast_notification({"title": data.title, "message": data.message, "channel": data.channel})
    return {"status": "sent", "count": count}
