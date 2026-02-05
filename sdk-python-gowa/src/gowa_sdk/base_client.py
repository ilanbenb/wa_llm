from __future__ import annotations

import base64
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel

DEVICE_HEADER = "X-Device-Id"


class GoWaBaseClient:
    def __init__(
        self,
        base_url: str = "http://localhost:3000",
        username: Optional[str] = None,
        password: Optional[str] = None,
        *,
        device_id: Optional[str] = None,
        timeout: float | httpx.Timeout = httpx.Timeout(300.0),
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        parsed_url = urlparse(base_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid base URL provided")

        self.base_url = base_url.rstrip("/")
        self.device_id = device_id

        default_headers = {"Accept": "application/json"}
        if username and password:
            auth_str = base64.b64encode(f"{username}:{password}".encode()).decode()
            default_headers["Authorization"] = f"Basic {auth_str}"
        if headers:
            default_headers.update(headers)

        self._headers = default_headers
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers,
            timeout=timeout,
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def __aenter__(self) -> "GoWaBaseClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    def with_device(self, device_id: str) -> "GoWaBaseClient":
        self.device_id = device_id
        return self

    def _build_headers(
        self,
        *,
        device_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        merged = dict(self._headers)
        if headers:
            merged.update(headers)
        final_device_id = device_id or self.device_id
        if final_device_id:
            merged[DEVICE_HEADER] = final_device_id
        return merged

    @staticmethod
    def _model_to_json(
        data: Optional[Dict[str, Any] | BaseModel],
    ) -> Optional[Dict[str, Any]]:
        if data is None:
            return None
        if isinstance(data, BaseModel):
            return data.model_dump(by_alias=True, exclude_none=True)
        return data

    @staticmethod
    def _coerce_form_value(value: Any) -> Any:
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return None
        return value

    def _model_to_form(
        self, data: Optional[Dict[str, Any] | BaseModel]
    ) -> Optional[Dict[str, Any]]:
        if data is None:
            return None
        if isinstance(data, BaseModel):
            raw = data.model_dump(by_alias=True, exclude_none=True)
        else:
            raw = {k: v for k, v in data.items() if v is not None}
        coerced = {
            k: self._coerce_form_value(v) for k, v in raw.items() if v is not None
        }
        return coerced or None

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any] | BaseModel] = None,
        data: Optional[Dict[str, Any] | BaseModel] = None,
        files: Optional[Dict[str, Any]] = None,
        device_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        request_headers = self._build_headers(device_id=device_id, headers=headers)
        json_payload = self._model_to_json(json)
        data_payload = self._model_to_form(data)

        response = await self.client.request(
            method,
            path,
            params=params,
            json=json_payload,
            data=data_payload,
            files=files,
            headers=request_headers,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if response.content:
                exc.args = (
                    f"{exc.args[0]}. Response content: {response.text}",
                ) + exc.args[1:]
            raise
        return response

    async def _get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        device_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        return await self._request(
            "GET", path, params=params, device_id=device_id, headers=headers
        )

    async def _post(
        self,
        path: str,
        *,
        json: Optional[Dict[str, Any] | BaseModel] = None,
        data: Optional[Dict[str, Any] | BaseModel] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        device_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        return await self._request(
            "POST",
            path,
            params=params,
            json=json,
            data=data,
            files=files,
            device_id=device_id,
            headers=headers,
        )

    async def _delete(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        device_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        return await self._request(
            "DELETE", path, params=params, device_id=device_id, headers=headers
        )
