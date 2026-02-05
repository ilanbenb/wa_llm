from __future__ import annotations

from typing import Optional

from ..models import (
    ApiResponse,
    DeviceCreateRequest,
    DeviceListResponse,
    DeviceLoginCodeRequest,
    DeviceStatusResponse,
    GenericResponse,
)
from ..protocols import GoWaClientProtocol


class DeviceMixin(GoWaClientProtocol):
    async def list_devices(self) -> DeviceListResponse:
        response = await self._get("/devices")
        return DeviceListResponse.model_validate_json(response.content)

    async def create_device(self, request: DeviceCreateRequest) -> ApiResponse[dict]:
        response = await self._post("/devices", json=request)
        return ApiResponse[dict].model_validate_json(response.content)

    async def get_device(self, device_id: str) -> ApiResponse[dict]:
        response = await self._get(f"/devices/{device_id}")
        return ApiResponse[dict].model_validate_json(response.content)

    async def delete_device(self, device_id: str) -> GenericResponse:
        response = await self._delete(f"/devices/{device_id}")
        return GenericResponse.model_validate_json(response.content)

    async def device_login_qr(self, device_id: str) -> ApiResponse[dict]:
        response = await self._get(f"/devices/{device_id}/login")
        return ApiResponse[dict].model_validate_json(response.content)

    async def device_login_code(
        self, device_id: str, request: DeviceLoginCodeRequest
    ) -> ApiResponse[dict]:
        response = await self._post(f"/devices/{device_id}/login/code", json=request)
        return ApiResponse[dict].model_validate_json(response.content)

    async def device_logout(self, device_id: str) -> GenericResponse:
        response = await self._post(f"/devices/{device_id}/logout")
        return GenericResponse.model_validate_json(response.content)

    async def device_reconnect(self, device_id: str) -> GenericResponse:
        response = await self._post(f"/devices/{device_id}/reconnect")
        return GenericResponse.model_validate_json(response.content)

    async def device_status(self, device_id: str) -> DeviceStatusResponse:
        response = await self._get(f"/devices/{device_id}/status")
        return DeviceStatusResponse.model_validate_json(response.content)
