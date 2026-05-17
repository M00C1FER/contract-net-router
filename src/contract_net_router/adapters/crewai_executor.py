"""Contract Net Protocol adapter for CrewAI."""
from .base import InMemoryCNPAdapter


class CrewAICNPAdapter(InMemoryCNPAdapter):
    """Contract Net Protocol adapter for CrewAI."""

    framework_name = "CrewAI"
