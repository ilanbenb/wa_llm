from typing import Any, Dict, Optional, Protocol, runtime_checkable
from pydantic import BaseModel
import httpx


@runtime_checkable
class WhatsAppClientProtocol(Protocol):
    async def _get(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> httpx.Response: ...

    async def _post(
        self,
        path: str,
        json: Optional[Dict[str, Any] | BaseModel] = None,
        data: Optional[Dict[str, Any] | BaseModel] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response: ...
