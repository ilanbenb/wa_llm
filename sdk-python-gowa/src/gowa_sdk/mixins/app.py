from __future__ import annotations

from typing import Optional

from ..models import (
    DeviceResponse,
    GenericResponse,
    LoginResponse,
    LoginWithCodeResponse,
    ApiResponse,
)
from ..protocols import GoWaClientProtocol


class AppMixin(GoWaClientProtocol):
    async def login(self, *, device_id: Optional[str] = None) -> LoginResponse:
        response = await self._get("/app/login", device_id=device_id)
        return LoginResponse.model_validate_json(response.content)

    async def login_with_code(
        self, phone: str, *, device_id: Optional[str] = None
    ) -> LoginWithCodeResponse:
        response = await self._get(
            "/app/login-with-code", params={"phone": phone}, device_id=device_id
        )
        return LoginWithCodeResponse.model_validate_json(response.content)

    async def logout(self, *, device_id: Optional[str] = None) -> GenericResponse:
        response = await self._get("/app/logout", device_id=device_id)
        return GenericResponse.model_validate_json(response.content)

    async def reconnect(self, *, device_id: Optional[str] = None) -> GenericResponse:
        response = await self._get("/app/reconnect", device_id=device_id)
        return GenericResponse.model_validate_json(response.content)

    async def get_devices(self, *, device_id: Optional[str] = None) -> DeviceResponse:
        response = await self._get("/app/devices", device_id=device_id)
        return DeviceResponse.model_validate_json(response.content)

    async def get_status(self, *, device_id: Optional[str] = None) -> ApiResponse[dict]:
        response = await self._get("/app/status", device_id=device_id)
        return ApiResponse[dict].model_validate_json(response.content)
