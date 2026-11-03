from app.ai.llm_client_api import generate_analysis
from app.ai.prompt_builder import build_prompt
from app.config.router import RouteResult, is_scope_request, route_question
from app.ai.context_builder import build_campaign_context, build_segment_context, build_campaign_comparison_context, build_insight_context
from app.utils.data_loader import get_campaign_data
import re
from app.services.rag_service import answer_with_rag

# Shared rule for laying out supporting evidence. Without it the model
# lists every metric for every item as separate bullets.
EVIDENCE_LAYOUT_RULES = """EVIDENCE LAYOUT

Use a Markdown table when the evidence compares 2 or more items (segments, campaigns,
customer tiers, countries, test vs control) and either:
- covers 2 or more metrics, or
- ranks 3 or more items.

Table rules:
- One row per item and one column per metric. The first column names the item.
- The second column is the metric the question asks about. If the question is general
  (for example "best" or "performed"), use the campaign's target KPI.
- Sort rows by that second column, best first.
- Use at most 6 metric columns and include only the metrics needed to answer the question.
- Use plain-language headers with units, for example "Absolute lift (pp)", "Marketing ROI",
  "Incremental revenue".
- Copy values exactly as they appear in the supplied data. Do not recalculate or reformat them.

Use short bullets ("Label: value") only for a single item or for at most 3 standalone values.
Never list the same metric once per item as separate bullets.

Example layout (placeholder names and values, not real data):

| Segment | Absolute lift (pp) | Marketing ROI |
|---|---|---|
| Segment A | 4.0 | 25.0% |
| Segment B | 2.0 | 10.0% |"""

STANDARD_RESPONSE_FORMAT = f"""Use the following format for every answer:

1. Begin with one direct conclusion written as a complete sentence. When the question is
   general (for example "Which segment performed best?"), name the campaign's target KPI
   in this sentence.
2. Only when supporting evidence is useful, continue with "The data shows:" followed by the
   evidence, laid out according to the EVIDENCE LAYOUT rules below.
3. Follow the evidence with two to four sentences explaining the trade-offs (scale,
   efficiency, incrementality) that support the conclusion.
4. Do not use bold text, italics, headings, or other markdown emphasis. Markdown tables are allowed.
5. Do not offer additional analysis at the end of the response.

{EVIDENCE_LAYOUT_RULES}
"""

INSIGHT_RESPONSE_FORMAT = f"""REQUIRED RESPONSE FORMAT

Respond using exactly these sections:
Use the following sub-headings:
## Campaign Assessment
## Key Insights
## What This Means
## Recommended Actions
## Limitations

Campaign Assessment
Provide a concise overall assessment of campaign performance.

Key Insights
When the findings compare segments or campaigns on metrics, start this section with one
compact table laid out according to the EVIDENCE LAYOUT rules below. Then:
1. State the most important finding.
2. State the next most important finding.
3. State another material finding, if supported.

What This Means
- Explain the business implications of the findings.

Recommended Actions
1. Provide a data-supported action.
2. Provide another data-supported action.
3. Include a monitoring or testing recommendation when appropriate.

Limitations
State any limitations in the supplied data or analysis.

Do not omit or rename these sections.
Do not begin with an unstructured summary.

{EVIDENCE_LAYOUT_RULES}"""

DERIVED_SIGNAL_RESPONSE_FORMAT = f"""Answer the user's specific question directly.
1. Answer key insights with full sentence.
2. Do not use bold text, italics, headings, or other markdown emphasis, except the
   section headings below. Markdown tables are allowed.

Use the following headings:
## Key Insights
## What This Means
## Limitations

Under Key Insights, when the answer compares segments or campaigns on metrics, include one
compact table laid out according to the EVIDENCE LAYOUT rules below.

Keep each section short and concise.
Only include Recommended Actions when the evidence supports a meaningful and specific action.
Do not expand into a broad campaign review.

{EVIDENCE_LAYOUT_RULES}"""

DERIVED_SIGNAL_PRIORITY_INSTRUCTIONS = """When the question asks for a top or bottom segment and this is an insight-scoped request, 
use only the DERIVED SEGMENT SIGNALS section for the ranking answer.
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

def _is_scope_request(question: str) -> bool:
    return is_scope_request(question)

def _get_response_format_instructions(context_type: str, question: str) -> str:
    if context_type == "insight":
        if _is_scope_request(question):
            return DERIVED_SIGNAL_RESPONSE_FORMAT
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
                route: RouteResult | None = None,
                ) -> str:
    """
    Build (or use) the context, fill the analyst prompt, and call the LLM.

    `route` is the route already decided by process_analyst_question. It is
    used as-is so a question is routed once (and follow-up rerouting is kept).
    It is only computed here when a caller doesn't pass one.
    """

    conversation_context = _format_conversation_history(conversation_history)

    if route is None:
        route = route_question(question)

    scope_request = is_scope_request(question)

    resolved_campaign_ids = route.campaign_ids or [campaign_id]
    resolved_campaign_id = resolved_campaign_ids[0]

    if context is None:
        data = get_campaign_data()
        summary_df, segment_df, campaign_goals_df = data.summary, data.segment, data.goals

        if route.context_type == "knowledge":
            return answer_with_rag(question)

        elif route.context_type == "campaign":
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
                None if scope_request and not route.campaign_ids else resolved_campaign_id
            )

        elif route.context_type in {"customer", "customer_campaign"}:
            # Customer questions are answered with guarded SQL; the context
            # is built by analyst_service._answer_customer_question.
            raise ValueError(
                "Customer-level questions must be routed through "
                "process_analyst_question()."
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
            "response_format_instructions": _get_response_format_instructions(route.context_type, question),
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
