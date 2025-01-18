import logging
import secrets
import string
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseSettings, Field

from .whatsapp_manager import WhatsAppConfig, WhatsAppManager


def generate_secure_secret(length: int = 32) -> str:
    alphabet = string.ascii_letters + string.digits + "-_"
    return "".join(secrets.choice(alphabet) for _ in range(length))


class WhatsAppSettings(BaseSettings):
    whatsapp_binary_path: str = "./whatsapp"
    whatsapp_port: int = 8080
    whatsapp_webhook_secret: str = Field(default_factory=generate_secure_secret)
    whatsapp_debug: bool = False
    whatsapp_os: str = "Chrome"
    whatsapp_basic_auth: str | None = None
    whatsapp_autoreply: str | None = None
    whatsapp_account_validation: bool = True
    whatsapp_db_uri: str = "file:storages/whatsapp.db?_foreign_keys=off"
    whatsapp_max_restarts: int = 3
    whatsapp_restart_delay: float = 5.0
    webhook_path: str = "/webhook"

    class Config:
        env_file = ".env"


class WhatsAppContext:
    def __init__(self, settings: WhatsAppSettings | None = None):
        self.settings = settings or WhatsAppSettings()
        self.manager = None
        self.logger = logging.getLogger("WhatsAppContext")
        self._webhook_secret = None

    @property
    def webhook_secret(self) -> str:
        if not self._webhook_secret:
            raise RuntimeError("Context not initialized")
        return self._webhook_secret

    def _create_config(self, webhook_url: str) -> WhatsAppConfig:
        self._webhook_secret = self.settings.whatsapp_webhook_secret

        return WhatsAppConfig(
            port=self.settings.whatsapp_port,
            webhook_url=webhook_url,
            webhook_secret=self._webhook_secret,
            debug=self.settings.whatsapp_debug,
            os_name=self.settings.whatsapp_os,
            basic_auth=self.settings.whatsapp_basic_auth,
            autoreply=self.settings.whatsapp_autoreply,
            account_validation=self.settings.whatsapp_account_validation,
            db_uri=self.settings.whatsapp_db_uri,
        )

    async def verify_secret(
        self, secret: str | None = Header(None, alias="X-Webhook-Secret")
    ) -> bool:
        if not secret:
            raise HTTPException(
                status_code=401, detail="Missing X-Webhook-Secret header"
            )
        if secret != self._webhook_secret:
            raise HTTPException(status_code=401, detail="Invalid webhook secret")
        return True

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        binary_path = Path(self.settings.whatsapp_binary_path)
        if not binary_path.exists() or not binary_path.is_file():
            raise RuntimeError(f"Invalid WhatsApp binary: {binary_path}")

        base_url = str(app.root_path).rstrip("/")
        webhook_path = self.settings.webhook_path
        if not webhook_path.startswith("/"):
            webhook_path = f"/{webhook_path}"

        config = self._create_config(f"{base_url}{webhook_path}")

        try:
            self.manager = WhatsAppManager(
                config=config,
                whatsapp_binary_path=str(binary_path),
                max_restarts=self.settings.whatsapp_max_restarts,
                restart_delay=self.settings.whatsapp_restart_delay,
            )

            await self.manager.start()
            yield

        finally:
            if self.manager:
                await self.manager.stop()
                self.manager = None

    def get_manager(self) -> WhatsAppManager:
        if not self.manager:
            raise RuntimeError("WhatsApp manager not initialized")
        return self.manager
