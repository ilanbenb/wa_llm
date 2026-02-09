from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from models import Group, BaseGroup, Sender, BaseSender, upsert
from .client import WhatsAppClient


async def gather_groups(session: AsyncSession, client: WhatsAppClient) -> None:
    groups = await client.get_user_groups()

    if groups is None or groups.results is None:
        return

    for g in groups.results.data:
        if not g.jid:
            continue
        owner_usr = g.owner_pn or g.owner_jid or None
        if owner_usr and (await session.get(Sender, owner_usr)) is None:
            owner = Sender(
                **BaseSender(
                    jid=owner_usr,
                ).model_dump()
            )
            await upsert(session, owner)

        existing_group = await session.get(Group, g.jid)

        group = Group(
            **BaseGroup(
                group_jid=g.jid,
                group_name=g.name,
                group_topic=g.topic,
                owner_jid=owner_usr,
                managed=existing_group.managed if existing_group else False,
                community_keys=existing_group.community_keys
                if existing_group
                else None,
                last_ingest=existing_group.last_ingest
                if existing_group
                else datetime.now(),
                last_summary_sync=existing_group.last_summary_sync
                if existing_group
                else datetime.now(),
                notify_on_spam=existing_group.notify_on_spam
                if existing_group
                else False,
                created_at=existing_group.created_at
                if existing_group
                else datetime.now(),
            ).model_dump()
        )
        await upsert(session, group)
