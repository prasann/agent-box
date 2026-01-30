"""AI agent client integration package."""

from .client import CustomCopilotClient, CopilotError, test_copilot_connection

__all__ = ["CustomCopilotClient", "CopilotError", "test_copilot_connection"]
