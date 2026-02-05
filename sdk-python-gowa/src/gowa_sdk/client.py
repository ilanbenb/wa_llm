from __future__ import annotations

from .base_client import GoWaBaseClient
from .mixins import (
    AppMixin,
    ChatMixin,
    DeviceMixin,
    GroupMixin,
    MessageMixin,
    NewsletterMixin,
    SendMixin,
    UserMixin,
)


class GoWaClient(
    GoWaBaseClient,
    AppMixin,
    DeviceMixin,
    UserMixin,
    SendMixin,
    MessageMixin,
    ChatMixin,
    GroupMixin,
    NewsletterMixin,
):
    """Async GoWa client combining all API mixins."""

    pass
