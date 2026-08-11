"""
Create priya@demo.com user directly in the database.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from database import async_session
from models import User, Business
from auth import get_password_hash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def main():
    async with async_session() as db:
        # Check if user exists
        result = await db.execute(select(User).where(User.email == "priya@demo.com"))
        existing = result.scalar_one_or_none()
        if existing:
            print(f"User already exists: {existing.id}")
            return
        
        # Create user
        user = User(
            email="priya@demo.com",
            password_hash=get_password_hash("123456"),
            full_name="Priya",
            phone="",
            role="customer",
        )
        db.add(user)
        await db.flush()
        
        # Create business
        business = Business(user_id=user.id, name="Priya's Business")
        db.add(business)
        await db.flush()
        await db.commit()
        
        print(f"User created: {user.id}")
        print(f"Business created: {business.id}")

asyncio.run(main())
