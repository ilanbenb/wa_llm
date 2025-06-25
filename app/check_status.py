import asyncio
import logging
import httpx
import logfire

from pydantic_settings import BaseSettings, SettingsConfigDict


class CheckStatusSettings(BaseSettings):
    base_url: str = "http://localhost:8000"
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        arbitrary_types_allowed=True,
        case_sensitive=False,
        extra="ignore",
    )


async def main():
    logger = logging.getLogger(__name__)

    settings = CheckStatusSettings()

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.DEBUG,
    )
    logfire.configure()
    logfire.instrument_pydantic_ai()
    logfire.instrument_httpx(capture_all=True)
    logfire.instrument_system_metrics()

    try:
        # Create an async HTTP client and forward the message
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{settings.base_url}/status",
            )
            response.raise_for_status()

    except httpx.HTTPError as exc:
        # Log the error but don't raise it to avoid breaking message processing
        logger.error(f"status check failed: {exc}")
        raise
    except Exception as exc:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error when calling status endpoint: {exc}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
