from dataclasses import dataclass
from typing import Union
from warnings import warn


class JIDParseError(Exception):
    """Exception raised for errors while parsing JIDs."""

    pass


@dataclass
class JID:
    user: str
    agent: int = 0
    device: int = 0
    server: str = ""
    ad: bool = False

    def user_int(self) -> int:
        return int(self.user)

    def to_non_ad(self) -> "JID":
        if self.ad:
            return JID(user=self.user, server=DefaultUserServer)
        else:
            return self

    def is_broadcast_list(self) -> bool:
        return self.server == BroadcastServer and self.user != StatusBroadcastJID.user

    def is_group(self) -> bool:
        return self.server == GroupServer

    def __str__(self) -> str:
        if self.ad:
            return f"{self.user}.{self.agent}:{self.device}@{self.server}"
        elif len(self.user) > 0:
            return f"{self.user}@{self.server}"
        else:
            return self.server

    def is_empty(self) -> bool:
        return len(self.server) == 0

    def normalize_str(self):
        return normalize_jid(self)


def new_ad_jid(user: str, agent: int, device: int) -> JID:
    return JID(user=user, agent=agent, device=device, server=DefaultUserServer, ad=True)


def parse_ad_jid(user: str) -> JID:
    full_jid = JID(user="", ad=True, server=DefaultUserServer)
    dot_index = user.find(".")
    colon_index = user.find(":")

    if dot_index < 0 or colon_index < 0 or colon_index + 1 <= dot_index:
        raise JIDParseError("failed to parse ADJID: missing separators") from None

    full_jid.user = user[:dot_index]

    try:
        agent = int(user[dot_index + 1 : colon_index])
        if agent < 0 or agent > 255:
            raise ValueError(f"invalid value ({agent})")
        device = int(user[colon_index + 1 :])
        if device < 0 or device > 255:
            raise ValueError(f"invalid value ({device})")
    except ValueError as err:
        raise JIDParseError(f"failed to parse agent/device from JID: {err}") from err

    full_jid.agent = agent
    full_jid.device = device
    return full_jid


def parse_jid(jid: str) -> JID:
    parts = jid.split("@")
    if len(parts) == 1:
        if not parts[0].isnumeric():
            raise JIDParseError(f"failed to parse JID: missing separator '@' in {jid}")
        return new_jid(parts[0], DefaultUserServer)
    elif ":" in parts[0]:
        if parts[1] == DefaultUserServer:
            if "." in parts[0]:
                return parse_ad_jid(parts[0])
            else:
                parts[0] = parts[0].split(":")[0]
    return new_jid(parts[0], parts[1])


def new_jid(user: str, server: str) -> JID:
    return JID(user=user, server=server)


def normalize_jid(jid: Union[JID, str]) -> str:
    if isinstance(jid, str):
        try:
            pjid = parse_jid(jid)
        except JIDParseError as err:
            warn(str(err))
            return jid
        jid = pjid

    return str(jid.to_non_ad())


# Known JID servers on WhatsApp
DefaultUserServer = "s.whatsapp.net"
GroupServer = "g.us"
LegacyUserServer = "c.us"
BroadcastServer = "broadcast"
HiddenUserServer = "lid"

# Some JIDs that are contacted often
EmptyJID = JID(user="")
GroupServerJID = new_jid("", GroupServer)
ServerJID = new_jid("", DefaultUserServer)
BroadcastServerJID = new_jid("", BroadcastServer)
StatusBroadcastJID = new_jid("status", BroadcastServer)
PSAJID = new_jid("0", LegacyUserServer)
OfficialBusinessJID = new_jid("16505361212", LegacyUserServer)
