"""The one executive-summary path used by every UI and by typed requests."""

import app.services.summary_service as summary_service
from app.utils.data_loader import get_campaign_data


def test_summary_uses_summary_prompt_model_and_campaign_context(monkeypatch):
    calls = []
    monkeypatch.setattr(
        summary_service, "generate_analysis",
        lambda prompt, purpose="answer": calls.append((prompt, purpose)) or "Summary.",
    )
    campaign_id = str(get_campaign_data().summary["campaign_id"].iloc[0])

    assert summary_service.generate_executive_summary(campaign_id) == "Summary."
    prompt, purpose = calls[0]
    assert purpose == "summary"
    assert f"Campaign ID: {campaign_id}" in prompt
    assert "## Key Strengths" in prompt
