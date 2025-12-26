import asyncio
import httpx
from datetime import datetime, timezone

WEBHOOK_URL = "http://localhost:8000/webhook"

async def send_webhook():
    # Payload simulating a message in the managed group, mentioning the bot
    # Bot JID: 972559913939@s.whatsapp.net
    # Group JID: 123456789@g.us (already set to managed=True)
    payload = {
        "from": "111111111111@s.whatsapp.net in 123456789@g.us",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pushname": "Test User",
        "message": {
            "id": "TEST_MSG_ID_GROUP_2",
            "text": "@972559913939 Who are you?" 
        }
    }

    print(f"Sending payload to {WEBHOOK_URL}...")
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(WEBHOOK_URL, json=payload)
            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text}")
        except httpx.ReadTimeout:
            print("Request timed out (server took too long to respond).")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(send_webhook())
