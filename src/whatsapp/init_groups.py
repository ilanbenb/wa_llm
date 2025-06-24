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
                ownerUsr = g.OwnerPN or g.OwnerJID or None
                if (await session.get(Sender, ownerUsr)) is None and ownerUsr:
                    owner = Sender(
                        **BaseSender(
                            jid=ownerUsr,
                        ).model_dump()
                    )
                    await upsert(session, owner)

                og = await session.get(Group, g.JID)

                group = Group(
                    **BaseGroup(
                        group_jid=g.JID,
                        group_name=g.Name,
                        group_topic=g.Topic,
                        owner_jid=ownerUsr,
                        managed=og.managed if og else False,
                        community_keys=og.community_keys if og else None,
                        last_ingest=og.last_ingest if og else datetime.now(),
                        last_summary_sync=og.last_summary_sync
                        if og
                        else datetime.now(),
                        forward_url=og.forward_url if og else None,
                        notify_on_spam=og.notify_on_spam if og else False,
                    ).model_dump()
                )
                await upsert(session, group)
            await session.commit()
        except Exception:
            await session.rollback()
            raise
