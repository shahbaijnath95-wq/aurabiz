from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from auth import get_current_user, verify_business_access
from models import User, Business, Customer
from schemas import CustomerCreate, CustomerUpdate, CustomerResponse, CustomerProfile, SuccessResponse
from services.customer_service import CustomerService
import csv
import io

router = APIRouter(prefix="/api/v1/customers", tags=["Customers"])


@router.get("/{business_id}")
async def list_customers(
    business_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    tag: str = Query(None),
    lifecycle_stage: str = Query(None),
    is_wholesaler: bool = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # IDOR protection: verify user owns this business
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    cs = CustomerService(db)
    filters = {}
    if tag:
        filters["tag"] = tag
    if lifecycle_stage:
        filters["lifecycle_stage"] = lifecycle_stage
    if is_wholesaler is not None:
        filters["is_wholesaler"] = is_wholesaler
    customers = await cs.search_customers(business_id, search or "", filters, page=page, limit=limit)

    return {
        "customers": [
            {
                "id": c.id, "phone_number": c.phone_number, "name": c.name,
                "email": c.email, "tags": c.tags, "lifecycle_stage": c.lifecycle_stage,
                "engagement_score": c.engagement_score, "total_orders": c.total_orders,
                "total_spent": c.total_spent, "loyalty_points": c.loyalty_points,
                "is_wholesaler": c.is_wholesaler,
            }
            for c in customers
        ],
        "total": len(customers),
        "page": page,
        "limit": limit,
    }


@router.get("/{id}/profile")
async def get_customer_profile(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cs = CustomerService(db)
    profile = await cs.get_customer_profile(id)
    if not profile:
        raise HTTPException(status_code=404, detail="Customer nahi mila")
    return profile


@router.post("")
async def create_customer(
    data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cs = CustomerService(db)
    # Check if customer with this phone number already exists for this business
    existing = await cs.search_customers(data.business_id, data.phone_number)
    for c in existing:
        if c.phone_number == data.phone_number:
            raise HTTPException(status_code=400, detail="Customer with this phone number already exists")
    
    customer = await cs.create_customer(data.model_dump())
    return {"status": "created", "customer_id": customer.id}

@router.put("/{id}")
async def update_customer(
    id: str,
    data: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cs = CustomerService(db)
    customer = await cs.update_customer(id, data.model_dump(exclude_unset=True))
    if not customer:
        raise HTTPException(status_code=404, detail="Customer nahi mila")
    return {"status": "updated", "customer_id": customer.id}


@router.post("/segment")
async def segment_customers(
    business_id: str = Query(...),
    criteria: dict = {},
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cs = CustomerService(db)
    segments = await cs.segment_customers(business_id, criteria)
    return segments


@router.get("/segments/{business_id}")
async def get_segments(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cs = CustomerService(db)
    return await cs.segment_customers(business_id, {})


@router.get("/import/sample-csv")
async def download_sample_csv():
    return {
        "headers": ["phone_number", "name", "email", "tags", "preferred_language"],
        "sample_rows": [
            ["+919876543210", "Rahul Sharma", "rahul@test.com", "vip,frequent", "hi"],
            ["+919876543211", "Priya Patel", "priya@test.com", "new", "hi"],
        ],
    }


@router.post("/import")
async def import_customers(
    data: dict,
    business_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cs = CustomerService(db)
    csv_data = data.get("csv_data", "")
    result = await cs.import_customers_csv(business_id, csv_data)
    return result


@router.get("/export")
async def export_customers(
    business_id: str = Query(...),
    format: str = Query("csv"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cs = CustomerService(db)
    path = await cs.export_customers(business_id, format)
    return {"file_path": path, "format": format}


@router.post("/merge")
async def merge_customers(
    primary_id: str,
    duplicate_ids: list[str],
    business_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cs = CustomerService(db)
    return await cs.merge_duplicates(business_id, primary_id, duplicate_ids)


@router.get("/search/{business_id}")
async def search_customers(
    business_id: str,
    q: str = Query(""),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cs = CustomerService(db)
    customers = await cs.search_customers(business_id, q)
    return {
        "results": [
            {"id": c.id, "name": c.name, "phone": c.phone_number, "lifecycle_stage": c.lifecycle_stage}
            for c in customers
        ]
    }
