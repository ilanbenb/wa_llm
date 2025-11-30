from sqlmodel import select, col
from sqlmodel.ext.asyncio.session import AsyncSession

from models import OptOut, Sender
from whatsapp.jid import normalize_jid


async def get_opt_out_map(session: AsyncSession, jids: list[str]) -> dict[str, str]:
    """
    Get a map of JID user part -> Display Name for users who have opted out.
    If a user has opted out but has no pushname, their number will be formatted with a space.
    """
    stmt = select(OptOut.jid).where(col(OptOut.jid).in_(jids))
    result = await session.exec(stmt)
    opted_out_jids = result.all()

    if not opted_out_jids:
        return {}

    # Get sender names for opted out users
    stmt = select(Sender).where(col(Sender.jid).in_(opted_out_jids))
    result = await session.exec(stmt)
    senders = result.all()
    sender_map = {s.jid: s.push_name for s in senders}

    opt_out_map = {}
    for jid in opted_out_jids:
        user_part = normalize_jid(jid).split("@")[0]
        if name := sender_map.get(jid):
            opt_out_map[user_part] = name
        else:
            # Format number with space to avoid tagging: 123456 -> 123 456
            if len(user_part) > 3:
                opt_out_map[user_part] = f"{user_part[:3]} {user_part[3:]}"
            else:
                opt_out_map[user_part] = user_part

    return opt_out_map
