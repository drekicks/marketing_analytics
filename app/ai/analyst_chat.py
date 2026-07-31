from app.ai.llm_client_api import generate_analysis
from app.ai.prompt_builder import build_prompt
from app.config.router import route_question
from app.ai.context_builder import build_campaign_context, build_segment_context, build_customer_context, build_campaign_comparison_context, build_insight_context
from app.ai.context_loader import summary_df, segment_df, campaign_goals_df, customer_df
import re

SCOPE_TERMS = (
    "overall",
    "across all",
    "across campaigns",
    "across segments",
    "portfolio-wide",
    "big picture",
    "holistically",
)

STANDARD_RESPONSE_FORMAT = """Use the following format for every answer:

1. Begin with one direct conclusion written as a complete sentence.
2. Do not use bold text, italics, headings, or other markdown emphasis.
3. Do not do this introduction if not showing campaign metrics. Only when showing supporting evidence is useful, introduce it with:
   \"The data shows\":
4. Present supporting evidence as a short-bulleted list.
5. Use plain-language labels followed by a colon and the metric value.
6. Do not offer additional analysis at the end of the response."""

INSIGHT_RESPONSE_FORMAT = """REQUIRED RESPONSE FORMAT

Respond using exactly these sections:

Campaign Assessment
Provide a concise overall assessment of campaign performance.

Key Insights
1. State the most important finding.
2. State the next most important finding.
3. State another material finding, if supported.

What This Means
Explain the business implications of the findings.

Recommended Actions
1. Provide a data-supported action.
2. Provide another data-supported action.
3. Include a monitoring or testing recommendation when appropriate.

Limitations
State any limitations in the supplied data or analysis.

Do not omit or rename these sections.
Do not begin with an unstructured summary."""

DERIVED_SIGNAL_PRIORITY_INSTRUCTIONS = """When the question asks for a top or bottom segment and this is an insight-scoped request, use only the DERIVED SEGMENT SIGNALS section for the ranking answer.
Return exactly one segment name for the requested rank and do not provide tied alternatives unless the derived signal itself explicitly shows a tie."""


def _get_derived_signal_metric_instruction(
    question: str,
    context_type: str,
) -> str | None:
    if context_type != "insight":
        return None

    normalized = question.lower()

    signal_label = None

    if "lowest" in normalized and "conversion rate" in normalized:
        signal_label = "Lowest conversion rate"
    elif "revenue per conversion" in normalized or "rpr" in normalized:
        signal_label = "Highest revenue per conversion"
    elif "absolute lift" in normalized or (
        "lift" in normalized and "conversion" not in normalized
    ):
        signal_label = "Highest absolute lift"
    elif "conversion rate" in normalized:
        signal_label = "Highest conversion rate"
    elif "conversion" in normalized or "conversions" in normalized:
        signal_label = "Most conversions"
    elif "revenue" in normalized:
        signal_label = "Most revenue"

    if not signal_label:
        return None

    return (
        "Include the metric value from DERIVED SEGMENT SIGNALS that matches "
        f"'{signal_label}'. Return the segment with that exact metric in "
        "parentheses using the same formatting shown there."
    )

# response_mode = get_insight_response_mode(question)

def _get_response_format_instructions(context_type: str) -> str:
    if context_type == "insight":
        return INSIGHT_RESPONSE_FORMAT

    return STANDARD_RESPONSE_FORMAT


def _should_prioritize_derived_signals(question: str, context_type: str) -> bool:
    if context_type != "insight":
        return False

    normalized = question.lower()

    asks_for_single_segment_rank = bool(
        re.search(
            r"which\s+segment.*\b(highest|lowest|most|least|best|worst)\b",
            normalized,
        )
    )

    asks_for_rank_without_which = bool(
        re.search(
            r"\b(highest|lowest|most|least|best|worst)\b.*\bsegment\b",
            normalized,
        )
    )

    return asks_for_single_segment_rank or asks_for_rank_without_which


def _build_question_with_instructions(question: str, context_type: str) -> str:
    if not _should_prioritize_derived_signals(question, context_type):
        return question

    metric_instruction = _get_derived_signal_metric_instruction(
        question,
        context_type,
    )

    extra_instructions = [DERIVED_SIGNAL_PRIORITY_INSTRUCTIONS]

    if metric_instruction:
        extra_instructions.append(metric_instruction)

    return f"{question}\n\n" + "\n".join(extra_instructions)

def ask_analyst(campaign_id: str,
                question: str,
                prompt_template: str,
                conversation_history: list[dict[str, str]],
                context: str | None = None,
                ) -> str:

    conversation_context = _format_conversation_history(conversation_history)

    route = route_question(question)
    normalized_question = question.lower()
    is_scope_request = any(term in normalized_question for term in SCOPE_TERMS)

    resolved_campaign_ids = route.campaign_ids or [campaign_id]
    resolved_campaign_id = resolved_campaign_ids[0]

    if context is None:
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

        elif route.context_type == "insight":
            context = build_insight_context(
                summary_df,
                segment_df,
                campaign_goals_df,
                None if is_scope_request and not route.campaign_ids else resolved_campaign_id
            )

        elif route.context_type in {"customer", "customer_campaign"}:
            context = build_customer_context(
                customer_df,
                campaign_goals_df,
                resolved_campaign_id
            )

        else:
            raise ValueError(
                f"Unsupported context type: {route.context_type}"
            )

    if not route.context_type:
        raise ValueError("No context was provided to analyst_chat().")

    final_prompt = build_prompt(
        template=prompt_template,
        variables={
            "response_format_instructions": _get_response_format_instructions(route.context_type),
            "campaign_context": context,
            "conversation_history": conversation_context,
            "question": _build_question_with_instructions(
                question,
                route.context_type,
            ),
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