from typing import Annotated
from fastapi import APIRouter, Depends
from .deps import get_db_async_session, get_whatsapp
router = APIRouter()

@router.get("/readiness")
async def status() -> dict[str, str]:
    return {"status": "ok"}



@router.get("/health")
async def health() -> dict[str, str]:
    session: Annotated[, Depends(get_db_async_session)],
    whatsapp: Annotated[WhatsAppClient, Depends(get_whatsapp)],
    return {"db": "ok",
            "whatsapp": "no_phone_number"}