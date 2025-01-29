from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API settings
    PORT: int = 5001
    HOST: str = "0.0.0.0"
    
    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "postgres"
    DB_USER: str = "postgres"
    DB_PASSWORD: str

    # WhatsApp settings
    MY_NUMBER: str
    WHATSAPP_HOST: str
    WHATSAPP_BASIC_AUTH_PASSWORD: Optional[str] = None
    WHATSAPP_BASIC_AUTH_USER: Optional[str] = None

    ANTHROPIC_API_KEY: str
    
    # Optional settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }

def get_settings() -> Settings:
    """Factory function to create Settings instance from environment variables."""
    # We ignore the pylance error because we want to fail the process if a required field is not provided.
    return Settings()  # type: ignore