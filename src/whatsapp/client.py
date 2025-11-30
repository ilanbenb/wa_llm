from .base_client import BaseWhatsAppClient
from .mixins import (
    AppMixin,
    UserMixin,
    MessageMixin,
    GroupMixin,
    NewsletterMixin,
)


class WhatsAppClient(
    BaseWhatsAppClient,
    AppMixin,
    UserMixin,
    MessageMixin,
    GroupMixin,
    NewsletterMixin,
):
    """
    WhatsApp Client combining all functionality
    """

    pass
