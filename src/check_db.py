import asyncio
from sqlmodel import select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from config import Settings
from models.group import Group

async def check_groups():
    settings = Settings()
    engine = create_async_engine(settings.db_uri)
    
    async with AsyncSession(engine) as session:
        # Check specifically for 'test group' or any group with threshold
        stmt = select(Group).where(Group.group_name == "test group")
        result = await session.exec(stmt)
        group = result.first()
        
        if group:
            print(f"Group: {group.group_name}")
            print(f"Threshold: {group.auto_summary_threshold}")
            print(f"Msg Count: {group.msg_count_since_last_summary}")
        else:
            print("Group 'test group' not found. Listing all groups with thresholds:")
            stmt = select(Group).where(Group.auto_summary_threshold > 0)
            result = await session.exec(stmt)
            groups = result.all()
            for g in groups:
                print(f"- {g.group_name}: Threshold={g.auto_summary_threshold}, Count={g.msg_count_since_last_summary}")

if __name__ == "__main__":
    asyncio.run(check_groups())
