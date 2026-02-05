from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel

from ..models import ApiResponse
from ..protocols import GoWaClientProtocol


class ChatMixin(GoWaClientProtocol):
    async def list_chats(
        self, *, params: Optional[Dict[str, Any]] = None, device_id: Optional[str] = None
    ) -> ApiResponse[dict]:
        response = await self._get("/chats", params=params, device_id=device_id)
        return ApiResponse[dict].model_validate_json(response.content)

    async def get_chat_messages(
        self,
        chat_jid: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        device_id: Optional[str] = None,
    ) -> ApiResponse[dict]:
        response = await self._get(
            f"/chat/{chat_jid}/messages", params=params, device_id=device_id
        )
        return ApiResponse[dict].model_validate_json(response.content)

    async def label_chat(
        self,
        chat_jid: str,
        payload: Dict[str, Any] | BaseModel,
        *,
        device_id: Optional[str] = None,
    ) -> ApiResponse[dict]:
        response = await self._post(
            f"/chat/{chat_jid}/label", json=payload, device_id=device_id
        )
        return ApiResponse[dict].model_validate_json(response.content)

    async def pin_chat(
        self,
        chat_jid: str,
        payload: Dict[str, Any] | BaseModel,
        *,
        device_id: Optional[str] = None,
    ) -> ApiResponse[dict]:
        response = await self._post(
            f"/chat/{chat_jid}/pin", json=payload, device_id=device_id
        )
        return ApiResponse[dict].model_validate_json(response.content)

    async def set_chat_disappearing(
        self,
        chat_jid: str,
        payload: Dict[str, Any] | BaseModel,
        *,
        device_id: Optional[str] = None,
    ) -> ApiResponse[dict]:
        response = await self._post(
            f"/chat/{chat_jid}/disappearing", json=payload, device_id=device_id
        )
        return ApiResponse[dict].model_validate_json(response.content)

    async def archive_chat(
        self,
        chat_jid: str,
        payload: Dict[str, Any] | BaseModel,
        *,
        device_id: Optional[str] = None,
    ) -> ApiResponse[dict]:
        response = await self._post(
            f"/chat/{chat_jid}/archive", json=payload, device_id=device_id
        )
        return ApiResponse[dict].model_validate_json(response.content)
