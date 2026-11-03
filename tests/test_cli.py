"""The CLI keeps conversation history and shows friendly errors."""

import builtins

import pytest

import app.ui.cli as cli
from app.config.settings import SessionState
from app.errors import LLMServiceError
from app.services.analyst_service import AnalystResult
from app.ui.errors import AI_UNAVAILABLE_MESSAGE


@pytest.fixture
def scripted_input(monkeypatch):
    lines: list[str] = []
    monkeypatch.setattr(builtins, "input", lambda prompt="": lines.pop(0))
    return lines


def _run(history):
    cli.run_cli_chat(
        session_state=SessionState(active_campaign_id="CMP-2026-004"),
        default_campaign_id="CMP-2026-004",
        valid_campaign_ids={"CMP-2026-004"},
        conversation_history=history,
    )


def test_history_grows_and_is_passed_to_follow_ups(monkeypatch, scripted_input, capsys):
    seen_history_lengths: list[int] = []

    def fake_process(**kwargs):
        seen_history_lengths.append(len(kwargs["conversation_history"]))
        return AnalystResult(answer=f"answer to {kwargs['question']}", campaign_id="CMP-2026-004")

    monkeypatch.setattr(cli, "process_analyst_question", fake_process)
    scripted_input.extend(["Which countries had the most converters?", "What about Canada?", "exit"])
    history: list[dict] = []

    _run(history)

    assert seen_history_lengths == [0, 1]
    assert [exchange["question"] for exchange in history] == [
        "Which countries had the most converters?",
        "What about Canada?",
    ]
    assert history[1]["answer"] == "answer to What about Canada?"


def test_errors_are_friendly_and_not_saved(monkeypatch, scripted_input, capsys):
    def failing_process(**kwargs):
        raise LLMServiceError("503")

    monkeypatch.setattr(cli, "process_analyst_question", failing_process)
    scripted_input.extend(["Which segment performed best?", "exit"])
    history: list[dict] = []

    _run(history)

    assert AI_UNAVAILABLE_MESSAGE in capsys.readouterr().out
    assert history == []
