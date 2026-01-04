import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from sqlmodel import select
from models.group import Group
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from config import get_settings

async def check_group(group_jid):
    settings = get_settings()
    # Force localhost port 5433 for host access
    db_uri = settings.db_uri.replace("5432", "5433")
    engine = create_async_engine(db_uri)
    
    async with AsyncSession(engine) as session:
        group = await session.get(Group, group_jid)
        if group:
            print(f"Group: {group.group_jid}")
            print(f"Name: {group.group_name}")
            print(f"Enable Web Search: {group.enable_web_search}")
            
            # Enable it
            group.enable_web_search = True
            session.add(group)
            await session.commit()
            print("Enabled Web Search for this group.")
        else:
            print(f"Group {group_jid} not found in DB")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_group("120363421803753507@g.us"))
