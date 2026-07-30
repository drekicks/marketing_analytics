import pytest

from app.config.router import route_question
from app.ai.context_builder import build_campaign_context, build_segment_context, build_customer_context


@pytest.mark.parametrize(
    ("question", "expected_context"),
    [
        (
            "Overall, which segment generated the highest lift?",
            "insight",
        ),
        # (
        #     "How was segment performance for CMP-2026-003?",
        #     "segment",
        # ),
        # (
        #     "How was performance by segment for CMP-2026-003?",
        #     "segment",
        # ),
        # (
        #     "Compare CMP-2026-004 and CMP-2026-003.",
        #     "campaign",
        # ),
        # (
        #     "Which segment performed best for CMP-2026-003?",
        #     "segment",
        # ),
        # (
        #     "Which customers responded to CMP-2026-003?",
        #     "customer_campaign",
        # ),
        # (
        #     "Break down CMP-2026-003 by segment.",
        #     "segment"
        #  ),
        # (
        #     "Show me the strongest audience group in CMP-2026-003.",
        #     "segment"
        #  ),
        # (
        #     "Which campaign performed better, CMP-2026-001 or CMP-2026-003?",
        #     "campaign"
        # ),
#         (
#             "Tell me about CMP-2026-003.",
#             "campaign"
#         ),
#         (
#             "What happened with CMP-2026-004?",
#             "insight"
#         ),
#         (
#             "Tell me what stands out about CMP-2026-003.",
#             "insight"
#         ),
#         (
#             "What are the key takeaways from CMP-2026-004 and CMP-2026-003?",
#             "insight"
#         ),
#         (
#             "Which email campaign had the highest revenue?",
#             "campaign"
#          ),
# (
#             "Overall, which segment had the highest revenue?",
#             "insight"
#          ),
#         (
#             "Which campaign had the highest revenue, CMP-2026-004 or CMP-2026-003?",
#             "campaign"
#         ),
#         (
#             "Across all campaigns, what delivered the most scale?",
#             "insight"
#         ),
#         (
#             "Overall, which segment had the highest conversion rate?",
#             "insight"
#         ),
#         (
#             "Which segment had the highest revenue?",
#             "segment"
#         )
    ],
)
def test_route_question(question, expected_context):
    route = route_question(question)

    assert route.context_type == expected_context


# def test_compare_question_with_two_campaign_ids_routes_as_comparison():
#     route = route_question("Compare CMP-2026-004 and CMP-2024-001")
#
#     assert route.context_type == "campaign"
#     assert route.analysis_type == "comparison"
#     assert route.campaign_ids == ["CMP-2026-004", "CMP-2024-001"]

# def test_segment_question_builds_segment_context():
#     question = "How was segment performance for CMP-2026-003?"
#
#     route = route_question(question)
#     context = build_campaign_context(route, datasets)
#
#     assert route.context_type == "segment"
#     assert "CMP-2026-003" in context
#     assert "Segment" in context
#     assert "Campaign Performance" not in context