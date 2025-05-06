import asyncio
from sqlalchemy import text
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from config import Settings

# Import all models to ensure they're registered with SQLModel
from models.group import Group  # This will trigger the model registration

async def init_db():
    settings = Settings()
    engine = create_async_engine(settings.db_uri)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await conn.run_sync(SQLModel.metadata.create_all)
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())

