from typing import TYPE_CHECKING
from ..protocols import WhatsAppClientProtocol

from ..models import (
    LoginResponse,
    LoginWithCodeResponse,
    GenericResponse,
    DeviceResponse,
)
from ..jid import JID, parse_jid
from typing import Optional

if TYPE_CHECKING:
    from ..base_client import BaseWhatsAppClient


class AppMixin(WhatsAppClientProtocol):
    async def login(self) -> LoginResponse:
        """Login to WhatsApp and get QR code"""
        response = await self._get("/app/login")
        return LoginResponse.model_validate_json(response.content)

    async def login_with_code(
        self, phone: str
    ) -> LoginWithCodeResponse:
        """Login with pairing code"""
        response = await self._get("/app/login-with-code", params={"phone": phone})
        return LoginWithCodeResponse.model_validate_json(response.content)

    async def logout(self) -> GenericResponse:
        """Logout and remove database"""
        response = await self._get("/app/logout")
        return GenericResponse.model_validate_json(response.content)

    async def reconnect(self) -> GenericResponse:
        """Reconnect to WhatsApp server"""
        response = await self._get("/app/reconnect")
        return GenericResponse.model_validate_json(response.content)

    async def get_devices(self) -> DeviceResponse:
        """Get list of connected devices"""
        response = await self._get("/app/devices")
        return DeviceResponse.model_validate_json(response.content)

    _jid: Optional[JID] = None

    async def get_my_jid(self) -> JID:
        if self._jid:
            return self._jid

        info = await self.get_devices()
        if not info.results:
            raise ValueError("No devices found")
        self._jid = parse_jid(info.results[0].device)
        return self._jid
