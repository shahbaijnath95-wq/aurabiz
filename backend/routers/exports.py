"""
Exports Router — CSV/JSON export for customers, orders, products, transactions.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import os

from database import get_db
from auth import get_current_user, verify_business_access
from models import User
from services.export_service import ExportService
from schemas import ExportRequest, ExportResponse

router = APIRouter(prefix="/api/v1/exports", tags=["Exports"])


@router.get("/stats/{business_id}")
async def export_stats(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = ExportService(db)
    return await svc.get_export_stats(business_id)


@router.get("/download/{export_id}")
async def download_export(export_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    svc = ExportService(db)
    job = await svc.get_export(export_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export nahi mila")
    if not await verify_business_access(current_user, job.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    if job.status != "completed" or not job.file_path:
        raise HTTPException(status_code=400, detail="Export abhi ready nahi hai")
    if not os.path.exists(job.file_path):
        raise HTTPException(status_code=404, detail="File nahi mili")
    media_type = "text/csv" if job.format == "csv" else "application/json"
    filename = os.path.basename(job.file_path)
    return FileResponse(job.file_path, media_type=media_type, filename=filename)


@router.get("/detail/{export_id}")
async def get_export(export_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    svc = ExportService(db)
    job = await svc.get_export(export_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export nahi mila")
    if not await verify_business_access(current_user, job.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    return {"id": job.id, "export_type": job.export_type, "format": job.format,
            "status": job.status, "row_count": job.row_count, "file_size": job.file_size}


@router.get("/{business_id}")
async def list_exports(business_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = ExportService(db)
    jobs = await svc.list_exports(business_id)
    return {"exports": [{"id": j.id, "export_type": j.export_type, "format": j.format,
                          "status": j.status, "row_count": j.row_count,
                          "file_size": j.file_size, "error_message": j.error_message,
                          "created_at": str(j.created_at) if j.created_at else None,
                          "completed_at": str(j.completed_at) if j.completed_at else None} for j in jobs]}


@router.post("")
async def create_export(data: ExportRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not await verify_business_access(current_user, data.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    svc = ExportService(db)
    job = await svc.create_export(data.business_id, data.export_type, data.format, data.filters)
    job = await svc.process_export(job.id)
    if job.status == "failed":
        raise HTTPException(status_code=500, detail=job.error_message)
    return {"id": job.id, "status": job.status, "row_count": job.row_count,
            "file_size": job.file_size, "message": "Export ho gaya!"}


@router.delete("/{export_id}")
async def delete_export(export_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    svc = ExportService(db)
    job = await svc.get_export(export_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export nahi mila")
    if not await verify_business_access(current_user, job.business_id, db):
        raise HTTPException(status_code=403, detail="Access denied")
    ok = await svc.delete_export(export_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Export nahi mila")
    return {"message": "Export delete ho gaya!"}

