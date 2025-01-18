import logging

import uvicorn
from fastapi import FastAPI, Depends, Request

from .whatsapp.fastapi_context import WhatsAppContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

whatsapp_context = WhatsAppContext()
app = FastAPI(lifespan=whatsapp_context.lifespan)

@app.post("/webhook")
async def webhook(request: Request, verified: bool = Depends(whatsapp_context.verify_secret)):
    data = await request.json()
    logger.info(f"Received webhook event: {data}")

    event_type = data.get('type')
    if event_type == 'message':
        return {"status": "message_processed"}
    elif event_type == 'status':
        return {"status": "status_processed"}

    return {"status": "unknown_event_type"}

@app.get("/health")
async def health_check():
    try:
        manager = whatsapp_context.get_manager()
        if not manager.process:
            return {"status": "unhealthy", "whatsapp": "not running"}
        return {"status": "healthy", "whatsapp": "running"}
    except RuntimeError:
        return {"status": "unhealthy", "whatsapp": "not initialized"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)