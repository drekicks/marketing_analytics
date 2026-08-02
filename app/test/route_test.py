from app.config.router import route_question
from app.ai.context_builder import build_campaign_context, build_segment_context, build_customer_context, build_insight_context
from app.utils.data_loader import summary_df, segment_df, campaign_goals_df, customer_df

questions = [
    "How was performance by segment for CMP-2026-003?",
    "How was segment performance for CMP-2026-003?",
    "Compare audience size for campaign CMP-2026-003 and CMP-2026-004",
    "Compare churn vs growth for campaign CMP-2026-003",
    "Compare churn vs growth segments for campaign CMP-2026-003 and CMP-2026-004",
    "Which campaign performed better, CMP-2026-004 or CMP-2026-003?",
    "How did CMP-2026-003 perform?",
    "Tell me what stands out about CMP-2026-003.",
    "What are the key takeaways from CMP-2026-004 and CMP-2026-003?",
    "Overall, which campaign performed better?",
    "Across all campaigns, which campaign had the highest conversion rate?",
    # "How did CMP-2026-999 perform?",
    # "Tell me about CMP-2026-999."
]

for question in questions:
    route = route_question(question)
    print(question, "->", route)

# question = "Compare segment churn vs growth?"
# route = route_question(question)
    campaign_id = route.campaign_ids[0] if route.campaign_ids else "CMP-2026-004"

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

    elif route.context_type == "insight":
        context = build_insight_context(
            summary_df,
            segment_df,
            campaign_goals_df,
            campaign_id
        )
    else:
        context = build_customer_context(
            customer_df,
            campaign_goals_df,
            campaign_id
        )

# print(route, campaign_id)