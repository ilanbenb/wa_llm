from __future__ import annotations

from typing import Optional

from gowa_sdk import GoWaClient

from .jid import JID, parse_jid


class WhatsAppClient(GoWaClient):
    """Thin wrapper over GoWaClient for app-specific helpers."""

    _jid: Optional[JID] = None

    async def get_my_jid(self) -> JID:
        if self._jid:
            return self._jid

        info = await self.get_devices()
        if not info.results:
            raise ValueError("No devices found")
        # Newer gowa versions return the WhatsApp JID in `jid` and an internal
        # device UUID in `device`; older versions put the JID in `device`.
        result = info.results[0]
        device_jid = getattr(result, "jid", None) or result.device
        if not device_jid:
            raise ValueError("No primary device JID found")
        self._jid = parse_jid(device_jid)
        return self._jid
