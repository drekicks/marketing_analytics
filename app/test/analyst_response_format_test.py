from app.ai.analyst_chat import (
    _get_response_format_instructions,
    INSIGHT_RESPONSE_FORMAT,
    STANDARD_RESPONSE_FORMAT,
)


def test_insight_context_uses_insight_response_format():
    response_format = _get_response_format_instructions("insight")

    assert response_format == INSIGHT_RESPONSE_FORMAT


def test_non_insight_context_uses_standard_response_format():
    response_format = _get_response_format_instructions("campaign")

    assert response_format == STANDARD_RESPONSE_FORMAT
