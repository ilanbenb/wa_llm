from typing import Any, Dict, Optional, Protocol, runtime_checkable

import httpx
from pydantic import BaseModel


@runtime_checkable
class GoWaClientProtocol(Protocol):
    async def _get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        device_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response: ...

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
    ) -> httpx.Response: ...

    async def _delete(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        device_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response: ...
