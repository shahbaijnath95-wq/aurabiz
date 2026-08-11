"""
Catalog Router — Product search, catalog browsing, recommendations.
Provides WhatsApp-formatted catalog responses.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from database import get_db
from auth import get_current_user, verify_business_access
from models import User
from services.catalog_service import CatalogService

router = APIRouter(prefix="/api/v1/catalog", tags=["Catalog"])


@router.get("/{business_id}")
async def get_catalog(
    business_id: str,
    category: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get paginated product catalog."""
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        service = CatalogService(db)
        result = await service.get_catalog(business_id, category, page, per_page)
        return result
    except Exception as e:
        logger.error("Catalog fetch error: {}", e)
        return {"products": [], "total": 0, "page": page, "per_page": per_page}


@router.get("/{business_id}/search")
async def search_products(
    business_id: str,
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search products by name, category, brand, or description."""
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        service = CatalogService(db)
        products = await service.search_products(business_id, q, limit)
        return {"products": products, "total": len(products), "query": q}
    except Exception as e:
        logger.error("Product search error: {}", e)
        return {"products": [], "total": 0, "query": q}


@router.get("/{business_id}/categories")
async def get_categories(
    business_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all product categories."""
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        service = CatalogService(db)
        categories = await service.get_categories(business_id)
        return {"categories": categories}
    except Exception as e:
        logger.error("Categories fetch error: {}", e)
        return {"categories": []}


@router.get("/{business_id}/recommendations")
async def get_recommendations(
    business_id: str,
    product_id: str = Query(None),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get product recommendations based on stock availability."""
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        service = CatalogService(db)
        products = await service.get_recommendations(business_id, product_id, limit)
        return {"recommendations": products}
    except Exception as e:
        logger.error("Recommendations error: {}", e)
        return {"recommendations": []}


@router.get("/{business_id}/whatsapp")
async def get_whatsapp_catalog(
    business_id: str,
    category: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get catalog formatted for WhatsApp messages."""
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        service = CatalogService(db)
        result = await service.get_catalog(business_id, category, page, per_page)
        products = result.get("products", [])
        whatsapp_text = service.format_catalog_for_whatsapp(products)
        return {"text": whatsapp_text, "products": products, "total": result.get("total", 0)}
    except Exception as e:
        logger.error("WhatsApp catalog error: {}", e)
        return {"text": "Catalog available nahi hai abhi.", "products": [], "total": 0}
