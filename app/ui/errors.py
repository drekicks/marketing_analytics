"""
User-facing error messages shared by the Streamlit app and the CLI.

Business and data problems are raised as ValueError with a message already
written for users. Everything else (AI service outages, database
connectivity, unexpected bugs) gets a short, friendly message here, and the
technical details go to the log instead of the screen.
"""

import logging

from sqlalchemy.exc import DBAPIError

from app.errors import ConfigurationError, LLMServiceError

logger = logging.getLogger(__name__)

AI_UNAVAILABLE_MESSAGE = (
    "The AI service didn't respond. Please try again in a moment."
)
DATABASE_UNAVAILABLE_MESSAGE = (
    "I couldn't reach the database. If it has been idle it may be waking up. "
    "Please try again."
)
UNEXPECTED_ERROR_MESSAGE = (
    "Something went wrong while answering. Please try again."
)


def user_message(error: Exception) -> str:
    """Return the message to show the user for an error."""
    if isinstance(error, (ValueError, ConfigurationError)):
        return str(error)

    if isinstance(error, LLMServiceError):
        logger.warning("AI service error: %s", error)
        return AI_UNAVAILABLE_MESSAGE

    if isinstance(error, DBAPIError):
        logger.warning("Database error: %s", error)
        return DATABASE_UNAVAILABLE_MESSAGE

    logger.exception("Unexpected error", exc_info=error)
    return UNEXPECTED_ERROR_MESSAGE
