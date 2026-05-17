"""Contract Net Protocol adapter for AutoGen."""
from .base import InMemoryCNPAdapter


class AutoGenCNPAdapter(InMemoryCNPAdapter):
    """Contract Net Protocol adapter for AutoGen."""

    framework_name = "AutoGen"
