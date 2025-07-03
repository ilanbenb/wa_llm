import asyncio
import logging

import logfire
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from config import Settings
from summarize_and_send_to_groups import summarize_and_send_to_groups
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

    whatsapp = WhatsAppClient(
        settings.whatsapp_host,
        settings.whatsapp_basic_auth_user,
        settings.whatsapp_basic_auth_password,
    )

    # Create engine with pooling configuration
    engine = create_async_engine(settings.db_uri)
    logfire.instrument_sqlalchemy(engine)

    async_session = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    async with async_session() as session:
        try:
            logging.info("Starting sync")
            await summarize_and_send_to_groups(session, whatsapp)
            await session.commit()
            logging.info("Finished sync")
        except Exception:
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
