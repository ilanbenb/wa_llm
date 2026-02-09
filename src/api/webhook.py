from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from api.deps import get_db_async_session, get_handler, get_whatsapp
from handler import MessageHandler
from gowa_sdk.webhooks import WebhookEnvelope
from whatsapp import WhatsAppClient
from whatsapp.init_groups import gather_groups

# Create router for webhook endpoints
router = APIRouter(tags=["webhook"])

MESSAGE_EVENTS = {"message", "message.reaction"}


def is_group_sync_event(event: str) -> bool:
    return event.lower().startswith("group.")


@router.post("/webhook")
async def webhook(
    payload: WebhookEnvelope,
    handler: Annotated[MessageHandler, Depends(get_handler)],
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
    whatsapp: Annotated[WhatsAppClient, Depends(get_whatsapp)],
) -> str:
    """
    WhatsApp webhook endpoint for receiving incoming messages.
    Returns:
        Simple "ok" response to acknowledge receipt
    """
    event = payload.event.lower()

    # Process message and reaction events through the message handler
    if event in MESSAGE_EVENTS:
        await handler(payload)

    # Keep GROUPS table in sync when group-related events happen
    if is_group_sync_event(event):
        await gather_groups(session, whatsapp)

    return "ok"
