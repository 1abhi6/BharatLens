# SQLAlchemy engine/session (async)
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL  # e.g. postgresql+asyncpg://user:pass@localhost:5432/dbname

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=settings.sqlalchemy_echo,
    future=True,
)

AsyncSessionLocal = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session