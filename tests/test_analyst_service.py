import pytest

import app.services.analyst_service as analyst_service
from app.config.settings import SessionState

VALID_CAMPAIGN_IDS = {"CMP-2025-002", "CMP-2026-003", "CMP-2026-004"}
ACTIVE_CAMPAIGN_ID = "CMP-2026-004"


@pytest.fixture
def ask_analyst_calls(monkeypatch, tmp_path):
    """Replace the LLM-backed ask_analyst and redirect charts to a temp dir."""
    calls: list[dict] = []

    def fake_ask_analyst(**kwargs):
        calls.append(kwargs)
        return f"answer-{len(calls)}"

    monkeypatch.setattr(analyst_service, "ask_analyst", fake_ask_analyst)
    monkeypatch.setattr(analyst_service, "chart_dir", tmp_path)
    return calls


def _ask(question: str):
    return analyst_service.process_analyst_question(
        question=question,
        session_state=SessionState(active_campaign_id=ACTIVE_CAMPAIGN_ID),
        default_campaign_id=ACTIVE_CAMPAIGN_ID,
        valid_campaign_ids=VALID_CAMPAIGN_IDS,
        conversation_history=[],
    )


@pytest.mark.parametrize(
    "question",
    [
        "Chart revenue by segment",
        "Chart conversion rate by segment",
        "Plot campaign revenue",
        "Plot campaign conversion rate",
    ],
)
def test_chart_question_returns_chart_interpretation(ask_analyst_calls, question):
    result = _ask(question)

    # Exactly one LLM call, made with the chart data as context.
    assert len(ask_analyst_calls) == 1
    assert ask_analyst_calls[0]["context"].startswith("VISUALIZATION DATA")

    # The returned answer is that chart interpretation, not a second answer.
    assert result.answer == "answer-1"
    assert result.chart_path is not None
    assert result.chart_path.exists()


def test_chart_filenames_are_unique_per_request(ask_analyst_calls):
    first = _ask("Chart revenue by segment")
    second = _ask("Chart revenue by segment")

    assert first.chart_path != second.chart_path


def test_non_chart_question_uses_normal_path(ask_analyst_calls):
    result = _ask("Which segment performed best?")

    assert len(ask_analyst_calls) == 1
    assert ask_analyst_calls[0]["context"] is None
    assert result.chart_path is None


def test_comparison_question_builds_comparison_context(ask_analyst_calls):
    _ask("Compare to CMP-2026-003")

    assert len(ask_analyst_calls) == 1
    context = ask_analyst_calls[0]["context"]
    assert context.startswith("CAMPAIGN COMPARISON CONTEXT")
    assert ACTIVE_CAMPAIGN_ID in context
    assert "CMP-2026-003" in context
