import asyncio
import httpx
import os
import sys
from datetime import datetime, timezone
from sqlmodel import select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

# DB URI from env or default to container internal address
DB_URI = os.getenv("DB_URI", "postgresql+asyncpg://user:password@postgres:5432/webhook_db")
WEBHOOK_URL = "http://localhost:8000/webhook"

async def setup_group():
    # Lazy import to avoid import errors if run outside of container without PYTHONPATH
    from models.group import Group

    print(f"Connecting to DB at {DB_URI}...")
    engine = create_async_engine(DB_URI)
    async with AsyncSession(engine) as session:
        group_jid = "123456789@g.us"
        
        # Check if group exists
        result = await session.exec(select(Group).where(Group.group_jid == group_jid))
        group = result.first()
        
        if not group:
            print(f"Creating group {group_jid}...")
            group = Group(group_jid=group_jid, managed=True)
            session.add(group)
        else:
            print(f"Updating group {group_jid} to managed=True...")
            group.managed = True
            session.add(group)
            
        await session.commit()
        print("Group setup complete.")
    
    await engine.dispose()

async def send_webhook():
    # Payload simulating a message in the managed group, mentioning the bot
    # Bot JID: 972559913939@s.whatsapp.net
    payload = {
        "from": "111111111111@s.whatsapp.net in 123456789@g.us",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pushname": "Test User",
        "message": {
            "id": "TEST_MSG_ID_GROUP_1",
            "text": "@972559913939 Who are you?" 
        }
    }

    print(f"Sending payload to {WEBHOOK_URL}...")
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(WEBHOOK_URL, json=payload)
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")

async def main():
    await setup_group()
    await send_webhook()

if __name__ == "__main__":
    asyncio.run(main())
