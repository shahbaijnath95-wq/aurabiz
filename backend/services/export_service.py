from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import ExportJob, Customer, Transaction, Order, Product
from datetime import datetime, timezone
import csv
import json
import os

EXPORT_DIR = "exports"


class ExportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_export(self, business_id: str, export_type: str, format: str = "csv",
                            filters: dict = None, requested_by: str = None) -> ExportJob:
        job = ExportJob(
            business_id=business_id,
            export_type=export_type,
            format=format,
            filters=filters or {},
            requested_by=requested_by,
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def process_export(self, job_id: str) -> ExportJob | None:
        result = await self.db.execute(select(ExportJob).where(ExportJob.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return None
        job.status = "processing"
        await self.db.commit()
        try:
            os.makedirs(EXPORT_DIR, exist_ok=True)
            rows = await self._fetch_data(job.business_id, job.export_type, job.filters)
            file_path = f"{EXPORT_DIR}/{job.export_type}_{job.business_id[:8]}_{int(datetime.now().timestamp())}.{job.format}"
            if job.format == "csv":
                await self._write_csv(file_path, rows)
            else:
                await self._write_json(file_path, rows)
            job.status = "completed"
            job.file_path = file_path
            job.row_count = len(rows)
            job.file_size = os.path.getsize(file_path)
            job.completed_at = datetime.now(timezone.utc)
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def _fetch_data(self, business_id: str, export_type: str, filters: dict) -> list[dict]:
        if export_type == "customers":
            result = await self.db.execute(
                select(Customer).where(Customer.business_id == business_id)
            )
            customers = result.scalars().all()
            return [
                {"id": c.id, "phone": c.phone_number, "name": c.name, "email": c.email,
                 "lifecycle_stage": c.lifecycle_stage, "total_orders": c.total_orders,
                 "total_spent": c.total_spent, "tags": json.dumps(c.tags or []),
                 "created_at": str(c.created_at)}
                for c in customers
            ]
        elif export_type == "transactions":
            result = await self.db.execute(
                select(Transaction).where(Transaction.business_id == business_id)
            )
            txns = result.scalars().all()
            return [
                {"id": t.id, "customer_id": t.customer_id, "type": t.type, "amount": t.amount,
                 "description": t.description, "status": t.status, "created_at": str(t.created_at)}
                for t in txns
            ]
        elif export_type == "orders":
            result = await self.db.execute(
                select(Order).where(Order.business_id == business_id)
            )
            orders = result.scalars().all()
            return [
                {"id": o.id, "customer_name": o.customer_name, "customer_phone": o.customer_phone,
                 "product_name": o.product_name, "quantity": o.quantity, "total_price": o.total_price,
                 "status": o.status, "delivery_type": o.delivery_type, "created_at": str(o.created_at)}
                for o in orders
            ]
        elif export_type == "products":
            result = await self.db.execute(
                select(Product).where(Product.business_id == business_id)
            )
            products = result.scalars().all()
            return [
                {"id": p.id, "name": p.name, "price": p.price, "description": p.description,
                 "category": p.category, "stock_quantity": getattr(p, "stock_quantity", 0),
                 "is_available": p.is_available, "created_at": str(p.created_at)}
                for p in products
            ]
        return []

    async def _write_csv(self, file_path: str, rows: list[dict]):
        if not rows:
            return
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    async def _write_json(self, file_path: str, rows: list[dict]):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2, default=str)

    async def get_export(self, export_id: str) -> ExportJob | None:
        result = await self.db.execute(select(ExportJob).where(ExportJob.id == export_id))
        return result.scalar_one_or_none()

    async def list_exports(self, business_id: str) -> list[ExportJob]:
        result = await self.db.execute(
            select(ExportJob).where(ExportJob.business_id == business_id).order_by(ExportJob.created_at.desc())
        )
        return result.scalars().all()

    async def delete_export(self, export_id: str) -> bool:
        job = await self.get_export(export_id)
        if not job:
            return False
        if job.file_path and os.path.exists(job.file_path):
            os.remove(job.file_path)
        await self.db.delete(job)
        await self.db.commit()
        return True

    async def get_export_stats(self, business_id: str) -> dict:
        total = await self.db.execute(
            select(func.count(ExportJob.id)).where(ExportJob.business_id == business_id)
        )
        completed = await self.db.execute(
            select(func.count(ExportJob.id)).where(ExportJob.business_id == business_id, ExportJob.status == "completed")
        )
        processing = await self.db.execute(
            select(func.count(ExportJob.id)).where(ExportJob.business_id == business_id, ExportJob.status == "processing")
        )
        failed = await self.db.execute(
            select(func.count(ExportJob.id)).where(ExportJob.business_id == business_id, ExportJob.status == "failed")
        )
        return {
            "total_jobs": total.scalar() or 0,
            "completed": completed.scalar() or 0,
            "processing": processing.scalar() or 0,
            "failed": failed.scalar() or 0,
        }
