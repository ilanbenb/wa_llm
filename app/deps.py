from typing import Annotated

from fastapi import Depends, Request
from sqlmodel.ext.asyncio.session import AsyncSession

from config import Settings
from handler import MessageHandler
from whatsapp import WhatsAppClient
from voyageai.client_async import AsyncClient


async def get_db_async_session(request: Request) -> AsyncSession:
    assert request.app.state.db_engine, "Database engine not initialized"
    async with AsyncSession(request.app.state.db_engine) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_whatsapp(request: Request) -> WhatsAppClient:
    assert request.app.state.whatsapp, "WhatsApp client not initialized"
    return request.app.state.whatsapp


def get_text_embebedding(request: Request) -> AsyncClient:
    assert request.app.state.embedding_client, "text embedding not initialized"
    return request.app.state.embedding_client


async def get_handler(
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
    whatsapp: Annotated[WhatsAppClient, Depends(get_whatsapp)],
    embedding_client: Annotated[AsyncClient, Depends(get_text_embebedding)],
) -> MessageHandler:
    return MessageHandler(session, whatsapp, embedding_client)
