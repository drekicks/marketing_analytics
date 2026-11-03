"""Knowledge (RAG) answers, with search and the LLM replaced by fakes."""

import pytest

import app.services.rag_service as rag_service
from app.errors import LLMServiceError


@pytest.fixture
def fake_search(monkeypatch):
    results: list[dict] = []
    monkeypatch.setattr(rag_service, "search_knowledge", lambda question, limit: results)
    return results


@pytest.fixture
def fake_llm(monkeypatch):
    prompts: list[str] = []

    def fake_generate_analysis(prompt):
        prompts.append(prompt)
        return "Churn Watchlist means customers who last purchased 61-175 days ago."

    monkeypatch.setattr(rag_service, "generate_analysis", fake_generate_analysis)
    return prompts


def test_answers_through_the_shared_llm_call(fake_search, fake_llm):
    fake_search.append({"similarity": 0.8, "content": "## Churn Watchlist\nPre-Lapsed customers."})

    answer = rag_service.answer_with_rag("What does Churn Watchlist mean?")

    assert answer.startswith("Churn Watchlist means")
    assert len(fake_llm) == 1
    assert "Pre-Lapsed customers." in fake_llm[0]
    assert "What does Churn Watchlist mean?" in fake_llm[0]


def test_low_similarity_returns_canned_answer_without_llm(fake_search, fake_llm):
    fake_search.append({"similarity": 0.1, "content": "Unrelated."})

    answer = rag_service.answer_with_rag("What is the weather?")

    assert answer == rag_service.NOT_ENOUGH_INFORMATION
    assert fake_llm == []


def test_no_results_returns_canned_answer(fake_search, fake_llm):
    assert rag_service.answer_with_rag("Anything?") == rag_service.NOT_ENOUGH_INFORMATION
    assert fake_llm == []


def test_llm_failure_surfaces_as_llm_service_error(fake_search, monkeypatch):
    fake_search.append({"similarity": 0.9, "content": "Definition."})

    def failing_generate_analysis(prompt):
        raise LLMServiceError("LLM request failed: 503")

    monkeypatch.setattr(rag_service, "generate_analysis", failing_generate_analysis)

    with pytest.raises(LLMServiceError):
        rag_service.answer_with_rag("What does Churn Watchlist mean?")


def test_rag_has_no_hard_coded_model():
    source = open(rag_service.__file__, encoding="utf-8").read()

    assert "gpt-" not in source
    assert "OpenAI(" not in source
