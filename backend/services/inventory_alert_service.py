from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import InventoryAlert, Product
from datetime import datetime, timezone


class InventoryAlertService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_alert(self, business_id: str, product_id: str = None, alert_type: str = "low_stock",
                           threshold: int = 5, message: str = None, notified_channels: list = None) -> InventoryAlert:
        current_stock = 0
        if product_id:
            result = await self.db.execute(select(Product).where(Product.id == product_id))
            product = result.scalar_one_or_none()
            if product:
                current_stock = getattr(product, "stock_quantity", 0) or 0

        alert = InventoryAlert(
            business_id=business_id,
            product_id=product_id,
            alert_type=alert_type,
            threshold=threshold,
            current_stock=current_stock,
            message=message or f"Stock is {current_stock} (threshold: {threshold})",
            notified_channels=notified_channels or ["dashboard"],
        )
        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def check_stock_alerts(self, business_id: str) -> list[InventoryAlert]:
        result = await self.db.execute(
            select(Product).where(Product.business_id == business_id)
        )
        products = result.scalars().all()
        new_alerts = []
        for p in products:
            stock = getattr(p, "stock_quantity", 0) or 0
            min_stock = getattr(p, "min_stock", 5) or 5
            if stock <= 0:
                existing = await self.db.execute(
                    select(InventoryAlert).where(
                        InventoryAlert.business_id == business_id,
                        InventoryAlert.product_id == p.id,
                        InventoryAlert.is_resolved == False,
                        InventoryAlert.alert_type == "out_of_stock",
                    )
                )
                if not existing.scalar_one_or_none():
                    alert = InventoryAlert(
                        business_id=business_id,
                        product_id=p.id,
                        alert_type="out_of_stock",
                        threshold=0,
                        current_stock=stock,
                        message=f"{p.name} is out of stock",
                        notified_channels=["dashboard", "whatsapp"],
                    )
                    self.db.add(alert)
                    new_alerts.append(alert)
            elif stock <= min_stock:
                existing = await self.db.execute(
                    select(InventoryAlert).where(
                        InventoryAlert.business_id == business_id,
                        InventoryAlert.product_id == p.id,
                        InventoryAlert.is_resolved == False,
                        InventoryAlert.alert_type == "low_stock",
                    )
                )
                if not existing.scalar_one_or_none():
                    alert = InventoryAlert(
                        business_id=business_id,
                        product_id=p.id,
                        alert_type="low_stock",
                        threshold=min_stock,
                        current_stock=stock,
                        message=f"{p.name} stock is low: {stock} remaining (min: {min_stock})",
                        notified_channels=["dashboard"],
                    )
                    self.db.add(alert)
                    new_alerts.append(alert)
        await self.db.commit()
        return new_alerts

    async def list_alerts(self, business_id: str, resolved: bool = None) -> list[InventoryAlert]:
        query = select(InventoryAlert).where(InventoryAlert.business_id == business_id)
        if resolved is not None:
            query = query.where(InventoryAlert.is_resolved == resolved)
        query = query.order_by(InventoryAlert.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def resolve_alert(self, alert_id: str) -> InventoryAlert | None:
        result = await self.db.execute(select(InventoryAlert).where(InventoryAlert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            return None
        alert.is_resolved = True
        alert.resolved_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def update_alert(self, alert_id: str, **kwargs) -> InventoryAlert | None:
        result = await self.db.execute(select(InventoryAlert).where(InventoryAlert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            return None
        for k, v in kwargs.items():
            if v is not None and hasattr(alert, k):
                setattr(alert, k, v)
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def delete_alert(self, alert_id: str) -> bool:
        result = await self.db.execute(select(InventoryAlert).where(InventoryAlert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            return False
        await self.db.delete(alert)
        await self.db.commit()
        return True

    async def get_alert_stats(self, business_id: str) -> dict:
        total = await self.db.execute(
            select(func.count(InventoryAlert.id)).where(InventoryAlert.business_id == business_id)
        )
        active = await self.db.execute(
            select(func.count(InventoryAlert.id)).where(
                InventoryAlert.business_id == business_id,
                InventoryAlert.is_resolved == False,
            )
        )
        return {
            "total": total.scalar() or 0,
            "active": active.scalar() or 0,
        }
