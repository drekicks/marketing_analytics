"""Per-purpose models and reasoning effort in the LLM client (API patched)."""

from types import SimpleNamespace

import pytest
from openai import BadRequestError

import app.ai.llm_client_api as llm
from app.errors import ConfigurationError, LLMServiceError


class FakeResponses:
    """Stands in for client.responses; records every create() call."""

    def __init__(self):
        self.calls: list[dict] = []
        self.reject_reasoning_for: set[str] = set()

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if "reasoning" in kwargs and kwargs["model"] in self.reject_reasoning_for:
            raise _bad_request("Unsupported parameter: 'reasoning.effort' is not supported with this model.")
        text = '{"sql": "select 1", "explanation": "x"}' if "text" in kwargs else "An answer."
        return SimpleNamespace(
            output_text=text,
            usage=SimpleNamespace(input_tokens=10, output_tokens=5),
        )


def _bad_request(message: str) -> BadRequestError:
    # A stand-in HTTP response: the SDK only reads these attributes, and this
    # keeps the test independent of which HTTP library the SDK build uses.
    response = SimpleNamespace(request=SimpleNamespace(), status_code=400, headers={})
    return BadRequestError(message, response=response, body=None)


@pytest.fixture
def fake_api(monkeypatch):
    fake = FakeResponses()
    monkeypatch.setattr(llm, "client", SimpleNamespace(responses=fake))
    monkeypatch.setattr(llm, "_no_reasoning_models", set())
    llm.configure_models(answer="answer-model", sql="sql-model", summary="summary-model", effort="low")
    yield fake
    llm.configure_models()
    llm.usage_log = None


def test_each_purpose_uses_its_model(fake_api):
    llm.generate_analysis("question prompt")
    llm.generate_analysis("summary prompt", purpose="summary")
    llm.generate_json("sql prompt", "customer_sql", {"type": "object"})

    assert [call["model"] for call in fake_api.calls] == ["answer-model", "summary-model", "sql-model"]


def test_reasoning_effort_is_sent(fake_api):
    llm.generate_analysis("prompt")

    assert fake_api.calls[0]["reasoning"] == {"effort": "low"}


def test_default_effort_sends_no_reasoning(fake_api):
    llm.configure_models(effort="default")

    llm.generate_analysis("prompt")

    assert "reasoning" not in fake_api.calls[0]


def test_invalid_effort_is_rejected(fake_api):
    with pytest.raises(ConfigurationError, match="Reasoning effort"):
        llm.configure_models(effort="turbo")


def test_rejected_reasoning_retries_once_and_is_remembered(fake_api):
    fake_api.reject_reasoning_for.add("answer-model")

    assert llm.generate_analysis("first") == "An answer."
    assert llm.generate_analysis("second") == "An answer."

    first, retry, second = fake_api.calls
    assert "reasoning" in first and "reasoning" not in retry
    # The model is remembered, so the next call skips reasoning straight away.
    assert "reasoning" not in second
    assert len(fake_api.calls) == 3


def test_other_bad_requests_are_not_retried(fake_api, monkeypatch):
    def failing_create(**kwargs):
        fake_api.calls.append(kwargs)
        raise _bad_request("Invalid model name")

    monkeypatch.setattr(fake_api, "create", failing_create)

    with pytest.raises(LLMServiceError):
        llm.generate_analysis("prompt")
    assert len(fake_api.calls) == 1


def test_overrides_fall_back_and_reset(fake_api):
    models = llm.configure_models(answer="mini")
    assert (models.answer, models.sql, models.summary) == ("mini", "mini", "mini")

    models = llm.configure_models(sql="strong")
    assert (models.answer, models.sql) == ("mini", "strong")

    reset = llm.configure_models()
    assert reset == llm._DEFAULT_MODELS


def test_usage_log_records_calls(fake_api):
    llm.usage_log = []

    llm.generate_analysis("prompt")

    entry = llm.usage_log[0]
    assert entry["purpose"] == "answer"
    assert entry["model"] == "answer-model"
    assert entry["effort"] == "low"
    assert (entry["input_tokens"], entry["output_tokens"]) == (10, 5)
    assert entry["seconds"] >= 0
