import asyncio
import logging

import logfire
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from config import Settings
from daily_ingest.daily_ingest import topicsLoader
from voyageai.client_async import AsyncClient

from whatsapp import WhatsAppClient


async def main():
    settings = Settings()

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=settings.log_level,
    )
    logfire.configure()
    logfire.instrument_pydantic_ai()
    logfire.instrument_httpx(capture_all=True)
    logfire.instrument_system_metrics()
    logfire.configure(scrubbing=False)

    whatsapp = WhatsAppClient(
        settings.whatsapp_host,
        settings.whatsapp_basic_auth_user,
        settings.whatsapp_basic_auth_password,
    )

    embedding_client = AsyncClient(api_key=settings.voyage_api_key, max_retries=5)

    # Create async engine using settings
    engine = create_async_engine(settings.db_uri)
    logfire.instrument_sqlalchemy(engine)
    async_session = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    # Create session with the async engine
    async with async_session() as session:
        topics_loader = topicsLoader()
        await topics_loader.load_topics_for_all_groups(
            session, embedding_client, whatsapp
        )

    # Clean up
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
