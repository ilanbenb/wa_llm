import base64
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel


class BaseWhatsAppClient:
    def __init__(
        self,
        base_url: str = "http://localhost:3000",
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: float | httpx.Timeout = httpx.Timeout(300.0),
    ):
        """
        Initialize WhatsApp Client

        Args:
            base_url: Base URL for the WhatsApp API
            username: Optional username for basic auth
            password: Optional password for basic auth
            timeout: Request timeout in seconds
        """
        # Validate and normalize base URL
        parsed_url = urlparse(base_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid base URL provided")
        self.base_url = base_url.rstrip("/")

        # Configure headers
        headers = {
            "Accept": "application/json",
        }

        # Add basic auth if credentials provided
        if username and password:
            auth_str = base64.b64encode(f"{username}:{password}".encode()).decode()  # noqa
            headers["Authorization"] = f"Basic {auth_str}"

        # Initialize httpx client with configuration
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        )

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def _get(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """
        Internal GET request method

        Args:
            path: API endpoint path
            params: Optional query parameters

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: If the request fails
        """
        response = await self.client.get(path, params=params)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if response.content:
                exc.args = (
                    f"{exc.args[0]}. Response content: {response.text}",
                ) + exc.args[1:]
            raise
        return response

    async def _post(
        self,
        path: str,
        json: Optional[Dict[str, Any] | BaseModel] = None,
        data: Optional[Dict[str, Any] | BaseModel] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """
        Internal POST request method

        Args:
            path: API endpoint path
            json: Optional JSON body
            data: Optional form data
            files: Optional files to upload

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: If the request fails
        """
        request_data: Any = data
        request_json: Any = json
        content: Any = None
        headers: Dict[str, str] = {}

        if isinstance(json, BaseModel):
            content = json.model_dump_json()
            headers = {"Content-Type": "application/json"}
            request_json = None
            request_data = None
        elif isinstance(data, BaseModel):
            content = data.model_dump_json()
            headers = {"Content-Type": "application/json"}
            request_data = None

        response = await self.client.post(
            path,
            json=request_json,
            data=request_data,
            content=content,
            files=files,
            headers=headers,
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
