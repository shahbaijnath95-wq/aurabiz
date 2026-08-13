"""
Create a test license in the SAME database that the master backend uses.
Previously this hardcoded a dev-machine path — the license never appeared
in the master backend's DB. Now it uses config.MASTER_DB_URL (AppData on
Windows, /var/lib/aurabiz or Postgres on servers).
"""
import os
import sys
import uuid
import asyncio
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from database import async_session, init_master_db
from models import Tenant, License
from sqlalchemy import select

TEST_LICENSE_KEY = os.getenv("TEST_LICENSE_KEY", "AURABIZ-TEST-1234-5678-ABCD")


async def main():
    await init_master_db()
    async with async_session() as db:
        # Check if already exists
        existing = await db.execute(select(License).where(License.license_key == TEST_LICENSE_KEY))
        if existing.scalar_one_or_none():
            print(f"License already exists: {TEST_LICENSE_KEY}")
            return

        tenant_result = await db.execute(select(Tenant).where(Tenant.owner_email == "test@example.com"))
        tenant = tenant_result.scalar_one_or_none()
        if not tenant:
            tenant = Tenant(
                slug=f"t{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}",
                name="Test Business",
                owner_name="Test User",
                owner_email="test@example.com",
                owner_phone=None,
                db_path="local-desktop-app",
                status="active",
                plan="starter",
                max_products=100,
                max_messages_per_month=500,
            )
            db.add(tenant)
            await db.flush()

        now = datetime.now(timezone.utc)
        lic = License(
            license_key=TEST_LICENSE_KEY,
            tenant_id=tenant.id,
            plan="starter",
            status="issued",
            max_activations=1,
            activations_used=0,
            owner_name="Test User",
            owner_email="test@example.com",
            owner_phone=None,
            amount_paid=999,
            ai_tier="free",
            paid_at=now,
            expires_at=now + timedelta(days=30),
            created_at=now,
        )
        db.add(lic)
        await db.commit()
        print(f"License created: {TEST_LICENSE_KEY}")
        print(f"Tenant: {tenant.id}")


if __name__ == "__main__":
    asyncio.run(main())