import time
from typing import Annotated, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import text

from whatsapp import WhatsAppClient

from .deps import get_db_async_session, get_whatsapp

router = APIRouter()


@router.get("/readiness")
async def readiness() -> Dict[str, str]:
    """Simple readiness check that returns immediately."""
    return {"status": "ok"}


@router.get("/status")
async def status(
    session: Annotated[AsyncSession, Depends(get_db_async_session)],
    whatsapp: Annotated[WhatsAppClient, Depends(get_whatsapp)],
) -> Dict[str, Any]:
    """
    Comprehensive health check that verifies:
    1. WhatsApp device connectivity (at least 1 device available)
    2. Database connection (simple query execution)

    Returns 200 if both checks pass, otherwise returns appropriate error status.
    """
    health_data = {"status": "healthy", "checks": {}, "timestamp": time.time()}

    # Track overall health status
    overall_healthy = True
    error_messages = []

    # Check 1: WhatsApp device connectivity
    devices_start_time = time.time()
    try:
        devices_response = await whatsapp.get_devices()
        devices_duration = time.time() - devices_start_time

        # Verify we have at least one device
        if not devices_response.results or len(devices_response.results) == 0:
            overall_healthy = False
            error_messages.append("No WhatsApp devices found")
            health_data["checks"]["whatsapp"] = {
                "status": "unhealthy",
                "error": "No devices available",
                "duration_seconds": devices_duration,
                "device_count": 0,
            }
        else:
            health_data["checks"]["whatsapp"] = {
                "status": "healthy",
                "duration_seconds": devices_duration,
                "device_count": len(devices_response.results),
                "devices": [
                    {"name": device.name, "device": device.device}
                    for device in devices_response.results
                ],
            }

    except Exception as e:
        devices_duration = time.time() - devices_start_time
        overall_healthy = False
        error_messages.append(f"WhatsApp device check failed: {str(e)}")
        health_data["checks"]["whatsapp"] = {
            "status": "unhealthy",
            "error": str(e),
            "duration_seconds": devices_duration,
        }

    # Check 2: Database connectivity
    db_start_time = time.time()
    try:
        # Execute a simple test query to verify database connectivity
        # Use connection() to get underlying SQLAlchemy connection for raw SQL
        conn = await session.connection()
        raw_result = await conn.execute(text("SELECT 1 + 1 as test_result"))
        test_value = raw_result.fetchone()
        db_duration = time.time() - db_start_time

        # Verify the query returned expected result
        if test_value and test_value[0] == 2:
            health_data["checks"]["database"] = {
                "status": "healthy",
                "duration_seconds": db_duration,
            }
        else:
            overall_healthy = False
            error_messages.append("Database query returned unexpected result")
            health_data["checks"]["database"] = {
                "status": "unhealthy",
                "error": "Query result validation failed",
                "duration_seconds": db_duration,
            }

    except Exception as e:
        db_duration = time.time() - db_start_time
        overall_healthy = False
        error_messages.append(f"Database connectivity check failed: {str(e)}")
        health_data["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
            "duration_seconds": db_duration,
        }

    # Calculate total duration
    health_data["total_duration_seconds"] = time.time() - health_data["timestamp"]

    # Return appropriate response based on health status
    if overall_healthy:
        return health_data
    else:
        # Update status to indicate issues
        health_data["status"] = "unhealthy"
        health_data["errors"] = error_messages

        # Return 503 Service Unavailable for health check failures
        # This is the most appropriate status for health check failures
        raise HTTPException(status_code=503, detail=health_data)
