import logging

from sqlalchemy.exc import OperationalError

from app.errors import ConfigurationError, LLMServiceError
from app.ui.errors import (
    AI_UNAVAILABLE_MESSAGE,
    DATABASE_UNAVAILABLE_MESSAGE,
    UNEXPECTED_ERROR_MESSAGE,
    user_message,
)


def test_value_errors_are_shown_as_written():
    assert user_message(ValueError("Campaign ID CMP-1 does not exist.")) == (
        "Campaign ID CMP-1 does not exist."
    )


def test_configuration_errors_are_shown_as_written():
    message = "OPENAI_MODEL is not configured. Add it to .env or the app secrets."

    assert user_message(ConfigurationError(message)) == message


def test_ai_failures_get_a_friendly_message():
    assert user_message(LLMServiceError("503 from API")) == AI_UNAVAILABLE_MESSAGE


def test_database_failures_get_a_friendly_message():
    error = OperationalError("connect", {}, Exception("could not connect to server"))

    assert user_message(error) == DATABASE_UNAVAILABLE_MESSAGE


def test_unexpected_errors_are_hidden_and_logged(caplog):
    with caplog.at_level(logging.ERROR, logger="app.ui.errors"):
        message = user_message(KeyError("segment_rpr"))

    assert message == UNEXPECTED_ERROR_MESSAGE
    assert "segment_rpr" not in message
    assert any("Unexpected error" in record.message for record in caplog.records)
