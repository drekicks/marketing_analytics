from app.config.router import route_question
from app.ai.context_builder import build_campaign_context, build_segment_context, build_customer_context, build_insight_context
from app.utils.data_loader import summary_df, segment_df, campaign_goals_df, customer_df
from app.ai.llm_client_api import generate_analysis
from app.ai.prompt_builder import build_prompt
from app.config.router import route_question
from app.ai.context_builder import (build_campaign_context, build_segment_context, build_customer_context,
                                    build_campaign_comparison_context, build_insight_context)
from app.utils.data_loader import summary_df, segment_df, campaign_goals_df, customer_df
from app.ai.insight_signals import (calculate_segment_signals,format_segment_signals,
                                    calculate_campaign_signals,format_campaign_signals)
import os

DATA_SOURCE = os.getenv("DATA_SOURCE",
                        "postgres",
                        ).strip().lower()

SCOPE_TERMS = (
    "overall",
    "across all",
    "across campaigns",
    "across segments",
    "portfolio-wide",
    "big picture",
    "holistically",
)

def _is_scope_request(question: str) -> bool:
    normalized = question.lower()
    return any(term in normalized for term in SCOPE_TERMS)

questions = [
    # "How was performance by segment for CMP-2026-003?",
    # "How was segment performance for CMP-2026-003?",
    "Compare audience size for campaign CMP-2026-003 and CMP-2026-004",
    # "Compare churn vs growth for campaign CMP-2026-003",
    # "Compare churn vs growth segments for campaign CMP-2026-003 and CMP-2026-004",
    # "Which campaign performed better, CMP-2026-004 or CMP-2026-003?",
    # "How did CMP-2026-003 perform?",
    # "Tell me what stands out about CMP-2026-003.",
    # "What are the key takeaways from CMP-2026-004 and CMP-2026-003?",
    "Overall, which campaign had highest revenue?",
    "Across all campaigns, which campaign had the highest conversion rate?",
    "Overall, which segment had highest revenue?",
    "Across all campaigns, which segment had the highest conversion rate?",
    # "How did CMP-2026-999 perform?",
    # "Tell me about CMP-2026-999."
]



for question in questions:
    route = route_question(question)
    print(question, "->", route)

# question = "Compare segment churn vs growth?"
# route = route_question(question)
    campaign_id = route.campaign_ids[0] if route.campaign_ids else "CMP-2026-004"
    is_scope_request = any(term in question for term in SCOPE_TERMS)

    if route.context_type == "campaign":
        context = build_campaign_context(
            summary_df,
            campaign_goals_df,
            campaign_id
        )

    elif route.context_type == "segment":
        context = build_segment_context(
            segment_df,
            campaign_goals_df,
            campaign_id
        )

    elif route.context_type == "insight" and route.subject == "segment":
        signals = calculate_segment_signals(segment_df)
        # print(f"Segment signals: {signals}")
        context = build_insight_context(
            summary_df,
            segment_df,
            campaign_goals_df,
            None if is_scope_request and not route.campaign_ids else campaign_id,
            signal_context=format_segment_signals(signals),
        )

    elif route.context_type == "insight" and route.subject == "campaign":
        signals = calculate_campaign_signals(summary_df)
        # print(f"Campaign signals: {signals}")
        context = build_insight_context(
            summary_df,
            segment_df,
            campaign_goals_df,
            None if is_scope_request and not route.campaign_ids else campaign_id,
            signal_context=format_campaign_signals(signals),
        )
    else:
        context = build_customer_context(
            customer_df,
            campaign_goals_df,
            campaign_id
        )

# print(route, campaign_id)