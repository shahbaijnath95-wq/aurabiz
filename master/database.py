"""Master Database Connection"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import MASTER_DB_URL

_connect_args = {}
if MASTER_DB_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_async_engine(MASTER_DB_URL, echo=False, connect_args=_connect_args)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_master_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_master_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)