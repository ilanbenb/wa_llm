from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from config import Settings
from db import init_db, get_messages_from_db
from webhook_logic import webhook_logic

# Load settings
settings = Settings()

# Initialize FastAPI app
app = FastAPI(title="Webhook API")

# Pydantic models for request/response validation
class WebhookResponse(BaseModel):
    status: str
    message: str
    id: int

class ErrorResponse(BaseModel):
    error: str
    message: Optional[str] = None
    details: Optional[str] = None

# Startup event
@app.on_event("startup")
async def startup_event():
    try:
        init_db()
    except Exception as e:
        print(f"Failed to initialize database: {e}")

@app.get("/")
async def hello_world() -> str:
    return "Hello, World!"

@app.post("/webhook", response_model=WebhookResponse)
async def webhook(payload: Dict[str, Any]) -> WebhookResponse:
    try:
        if not payload:
            raise HTTPException(
                status_code=400, 
                detail="No payload received"
            )

        message_id = webhook_logic(payload)
        
        return WebhookResponse(
            status="success",
            message="Webhook received and stored and handled",
            id=message_id
        )
    
    except ValueError as validation_error:
        raise HTTPException(
            status_code=400,
            detail=str(validation_error)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process webhook: {str(e)}"
        )

@app.get("/messages")
async def get_messages() -> list:
    try:
        messages = get_messages_from_db()
        return messages
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve messages: {str(e)}"
        )

if __name__ == "__main__":
    app.run(debug=True, host=host, port=port)
