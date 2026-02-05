from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class WebhookBaseModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        try:
            normalized = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError as exc:
            raise ValueError("timestamp must be RFC3339 or epoch seconds") from exc
    raise ValueError("timestamp must be RFC3339 or epoch seconds")


class WebhookEnvelope(WebhookBaseModel):
    event: str = Field(validation_alias=AliasChoices("event", "event_type"))
    device_id: Optional[str] = None
    payload: Dict[str, Any] = Field(
        default_factory=dict, validation_alias=AliasChoices("payload", "data")
    )
    timestamp: Optional[datetime] = None

    @field_validator("timestamp", mode="before")
    @classmethod
    def _validate_timestamp(cls, value: Any) -> Optional[datetime]:
        return _parse_timestamp(value)

    def parse_payload(self, model: type[BaseModel]) -> BaseModel:
        return model.model_validate(self.payload)


class WebhookMessagePayload(WebhookBaseModel):
    id: Optional[str] = None
    chat_id: Optional[str] = None
    from_: Optional[str] = Field(default=None, alias="from")
    from_lid: Optional[str] = None
    from_name: Optional[str] = None
    timestamp: Optional[datetime] = None
    text: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("text", "message", "body")
    )
    reaction: Optional[str] = None
    reacted_message_id: Optional[str] = None
    replied_to_id: Optional[str] = None
    quoted_body: Optional[str] = None

    @field_validator("timestamp", mode="before")
    @classmethod
    def _validate_timestamp(cls, value: Any) -> Optional[datetime]:
        return _parse_timestamp(value)


class WebhookAckPayload(WebhookBaseModel):
    id: Optional[str] = None
    chat_id: Optional[str] = None
    status: Optional[str] = None
    timestamp: Optional[datetime] = None
    participant: Optional[str] = None

    @field_validator("timestamp", mode="before")
    @classmethod
    def _validate_timestamp(cls, value: Any) -> Optional[datetime]:
        return _parse_timestamp(value)


class WebhookGroupParticipantPayload(WebhookBaseModel):
    group_id: Optional[str] = None
    action: Optional[str] = None
    participants: Optional[list[str]] = None


class WebhookGroupUpdatePayload(WebhookBaseModel):
    group_id: Optional[str] = None
    action: Optional[str] = None
    actor: Optional[str] = None
    value: Optional[str] = None


class WebhookNewsletterPayload(WebhookBaseModel):
    id: Optional[str] = None
    newsletter_id: Optional[str] = None
    sender: Optional[str] = None
    text: Optional[str] = None


def parse_webhook(payload: str | bytes | Dict[str, Any]) -> WebhookEnvelope:
    if isinstance(payload, (str, bytes)):
        return WebhookEnvelope.model_validate_json(payload)
    return WebhookEnvelope.model_validate(payload)
