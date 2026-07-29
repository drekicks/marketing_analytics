import pytest

from app.config.router import route_question
from app.ai.context_builder import build_campaign_context, build_segment_context, build_customer_context


@pytest.mark.parametrize(
    ("question", "expected_context"),
    [
        (
            "How did CMP-2026-003 perform?",
            "campaign",
        ),
        (
            "How was segment performance for CMP-2026-003?",
            "segment",
        ),
        (
            "How was performance by segment for CMP-2026-003?",
            "segment",
        ),
        (
            "Compare CMP-2026-001 and CMP-2026-003.",
            "campaign",
        ),
        (
            "Which segment performed best for CMP-2026-003?",
            "segment",
        ),
        (
            "Which customers responded to CMP-2026-003?",
            "customer_campaign",
        ),
        (
            "Break down CMP-2026-003 by segment.",
            "segment"
         ),
        (
            "Show me the strongest audience group in CMP-2026-003.",
            "segment"
         ),
        (
            "Which campaign performed better, CMP-2026-001 or CMP-2026-003?",
            "campaign"
        ),
        (
            "Tell me about CMP-2026-003.",
            "campaign"
        ),
        (
            "What happened with CMP-2026-004?",
            "campaign"
        ),

    ],
)
def test_route_question(question, expected_context):
    route = route_question(question)

    assert route.context_type == expected_context

def test_segment_question_builds_segment_context():
    question = "How was segment performance for CMP-2026-003?"

    route = route_question(question)
    context = build_campaign_context(route, datasets)

    assert route.context_type == "segment"
    assert "CMP-2026-003" in context
    assert "Segment" in context
    assert "Campaign Performance" not in context