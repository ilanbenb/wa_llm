import logging
from typing import Annotated, Dict, Any
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from whatsapp import WhatsAppClient
from daily_summary_sync import daily_summary_sync
from .deps import get_db_async_session, get_whatsapp

# Create router for daily summary endpoints
router = APIRouter()

# Configure logger for this module
logger = logging.getLogger(__name__)


@router.post("/daily_summary")
async def trigger_daily_summary(
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
    whatsapp: Annotated[WhatsAppClient, Depends(get_whatsapp)],
) -> Dict[str, Any]:
    """
    Trigger a daily summary sync for all managed groups.
    
    This endpoint manually triggers the same process that runs
    in the daily_summary.py script. It will:
    1. Find all managed groups
    2. Check for new messages since last summary
    3. Generate AI summaries for groups with enough new messages
    4. Send summaries to the groups and related community groups
    5. Update the last_summary_sync timestamp
    
    Returns a success message upon completion.
    """
    try:
        logger.info("Starting manual daily summary sync via API")
        
        # Execute the daily summary sync process
        await daily_summary_sync(session, whatsapp)
        
        logger.info("Daily summary sync completed successfully")
        
        return {
            "status": "success",
            "message": "Daily summary sync completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error during daily summary sync: {str(e)}")
        # Re-raise the exception to let FastAPI handle it with proper error response
        raise 