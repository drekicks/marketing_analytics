from app.ai.llm_client_api import generate_analysis
from app.ai.prompt_builder import build_prompt
from app.config.router import route_question
from app.ai.context_builder import build_campaign_context, build_segment_context, build_customer_context, build_campaign_comparison_context
from app.ai.context_loader import summary_df, segment_df, campaign_goals_df, customer_df

def ask_analyst(campaign_id: str,
                question: str,
                prompt_template: str,
                conversation_history: list[dict[str, str]]
                ) -> str:

    conversation_context = _format_conversation_history(conversation_history)

    route = route_question(question)

    resolved_campaign_ids = route.campaign_ids or [campaign_id]
    resolved_campaign_id = resolved_campaign_ids[0]

    if route.context_type == "campaign":
        if route.analysis_type == "comparison" and len(resolved_campaign_ids) >= 2:
            context = build_campaign_comparison_context(
                summary_df,
                campaign_goals_df,
                resolved_campaign_ids,
            )
        else:
            context = build_campaign_context(
                summary_df,
                campaign_goals_df,
                resolved_campaign_id
            )

    elif route.context_type == "segment":
        context = build_segment_context(
            segment_df,
            campaign_goals_df,
            resolved_campaign_id
        )

    else:
        context = build_customer_context(
            customer_df,
            campaign_goals_df,
            resolved_campaign_id
        )

    final_prompt = build_prompt(
        template=prompt_template,
        variables={
            "campaign_context": context,
            "conversation_history": conversation_context,
            "question": question,
        },
    )

    return generate_analysis(final_prompt)

def _format_conversation_history(
    conversation_history: list[dict[str, str]],
    max_exchanges: int = 5,
) -> str:
    if not conversation_history:
        return ""

    recent_history = conversation_history[-max_exchanges:]

    formatted_exchanges = []

    for exchange in recent_history:
        formatted_exchanges.append(
            f"User: {exchange['question']}\n"
            f"Analyst: {exchange['answer']}"
        )

    return "\n\n".join(formatted_exchanges)

# template = load_prompt("executive_summary")
# a = ask_analyst(campaign_id="CMP-2026-004", question="Compare segment churn vs growth?", prompt_template=template, conversation_history=[])
# print(a)