from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from auth import get_current_user
from models import User, Business
from schemas import WhatsAppTemplateCreate, SuccessResponse
from services.template_manager import TemplateManager

router = APIRouter(prefix="/api/v1/whatsapp/templates", tags=["WhatsApp Templates"])


@router.get("")
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    business_result = await db.execute(select(Business).where(Business.user_id == current_user.id))
    business = business_result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business nahi mila")
    tm = TemplateManager(db)
    templates = await tm.get_templates(business.id)
    return {"templates": [{"id": t.id, "name": t.name, "category": t.category, "body": t.body, "status": t.status} for t in templates]}


@router.post("")
async def create_template(
    data: WhatsAppTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    business_result = await db.execute(select(Business).where(Business.user_id == current_user.id))
    business = business_result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business nahi mila")
    tm = TemplateManager(db)
    template = await tm.create_template(business.id, data.model_dump())
    return {"status": "created", "template_id": template.id}


@router.put("/{id}")
async def update_template(
    id: str,
    data: WhatsAppTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tm = TemplateManager(db)
    template = await tm.update_template(id, data.model_dump(exclude_unset=True))
    if not template:
        raise HTTPException(status_code=404, detail="Template nahi mili")
    return {"status": "updated"}


@router.delete("/{id}")
async def delete_template(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tm = TemplateManager(db)
    result = await tm.delete_template(id)
    return {"status": "deleted" if result else "not_found"}


@router.post("/{id}/preview")
async def preview_template(
    id: str,
    variables: dict = {},
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tm = TemplateManager(db)
    preview = await tm.preview_template(id, variables)
    return {"preview": preview}


@router.get("/categories")
async def get_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tm = TemplateManager(db)
    return {"categories": await tm.get_categories()}


@router.post("/{id}/test")
async def test_template(
    id: str,
    phone_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tm = TemplateManager(db)
    return await tm.send_test(id, phone_number)
