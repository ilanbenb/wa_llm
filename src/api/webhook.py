from typing import Annotated

from fastapi import APIRouter, Depends

from api.deps import get_handler
from handler import MessageHandler
from gowa_sdk.webhooks import WebhookEnvelope

# Create router for webhook endpoints
router = APIRouter(tags=["webhook"])


@router.post("/webhook")
async def webhook(
    payload: WebhookEnvelope,
    handler: Annotated[MessageHandler, Depends(get_handler)],
) -> str:
    """
    WhatsApp webhook endpoint for receiving incoming messages.
    Returns:
        Simple "ok" response to acknowledge receipt
    """
    # Only process message and reaction events
    if payload.event in {"message", "message.reaction"}:
        await handler(payload)

    return "ok"
