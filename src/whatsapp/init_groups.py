import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession

from models import Group, BaseGroup, Sender, BaseSender, GroupMember, upsert, bulk_upsert
from .client import WhatsAppClient

logger = logging.getLogger(__name__)


async def gather_groups(db_engine: AsyncEngine, client: WhatsAppClient):
    try:
        groups = await client.get_user_groups()
    except Exception as e:
        logger.error(f"Failed to gather groups: {e}")
        return

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
                        notify_on_spam=og.notify_on_spam if og else False,
                        created_at=og.created_at if og else datetime.now(),
                        auto_summary_threshold=og.auto_summary_threshold if og else None,
                        msg_count_since_last_summary=og.msg_count_since_last_summary if og else 0,
                        enable_web_search=og.enable_web_search if og else False,
                    ).model_dump()
                )
                await upsert(session, group)

                # Collect participants for bulk upsert
                senders_map = {}
                group_members = []

                if g.Participants:
                    for p in g.Participants:
                        # Prepare Sender
                        if p.JID not in senders_map:
                            senders_map[p.JID] = Sender(
                                **BaseSender(
                                    jid=p.JID,
                                    push_name=p.DisplayName,
                                ).model_dump()
                            )

                        # Prepare GroupMember
                        group_members.append(
                            GroupMember(
                                group_jid=g.JID,
                                sender_jid=p.JID,
                                role="admin"
                                if p.IsAdmin
                                else ("superadmin" if p.IsSuperAdmin else "participant"),
                            )
                        )

                # Perform bulk upserts
                if senders_map:
                    await bulk_upsert(session, list(senders_map.values()))
                if group_members:
                    await bulk_upsert(session, group_members)

            await session.commit()
        except Exception:
            await session.rollback()
            raise
