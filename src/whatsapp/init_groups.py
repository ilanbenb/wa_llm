from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession

from models import Group, BaseGroup, Sender, BaseSender, upsert
from .client import WhatsAppClient


async def gather_groups(db_engine: AsyncEngine, client: WhatsAppClient):
    groups = await client.get_user_groups()

    async with AsyncSession(db_engine) as session:
        try:
            if groups is None or groups.results is None:
                return
            for g in groups.results.data:
                ownerUsr = g.owner_pn or g.owner_jid or None
                if (await session.get(Sender, ownerUsr)) is None and ownerUsr:
                    owner = Sender(
                        **BaseSender(
                            jid=ownerUsr,
                        ).model_dump()
                    )
                    await upsert(session, owner)

                og = await session.get(Group, g.jid)

                group = Group(
                    **BaseGroup(
                        group_jid=g.jid,
                        group_name=g.name,
                        group_topic=g.topic,
                        owner_jid=ownerUsr,
                        managed=og.managed if og else False,
                        community_keys=og.community_keys if og else None,
                        last_ingest=og.last_ingest if og else datetime.now(),
                        last_summary_sync=og.last_summary_sync
                        if og
                        else datetime.now(),
                        notify_on_spam=og.notify_on_spam if og else False,
                        created_at=og.created_at if og else datetime.now(),
                    ).model_dump()
                )
                await upsert(session, group)
            await session.commit()
        except Exception:
            await session.rollback()
            raise
