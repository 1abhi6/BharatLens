import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import engine, get_async_session
from app.models import user, chat_session, message  # ensure models are imported so tables exist
from app.db.base import Base


async def test_connection():
    # Try creating tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Database connected and tables created successfully!")

    # Try a session commit/rollback test
    async for session in get_async_session():
        if isinstance(session, AsyncSession):
            print("✅ AsyncSession is working!")
        break


if __name__ == "__main__":
    asyncio.run(test_connection())
