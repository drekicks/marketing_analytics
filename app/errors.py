"""
Application exception types.

Kept free of other app imports so the UIs can import them even when
configuration or data loading fails at start-up.
"""


class ConfigurationError(RuntimeError):
    """Required settings are missing or invalid. The message is user-facing."""


class LLMServiceError(RuntimeError):
    """
    The AI service failed: API error, empty reply, or unusable output.

    Raised for problems the user can't fix by rephrasing (unlike ValueError).
    The UIs show a generic "AI service didn't respond" message for it.
    """
