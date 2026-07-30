from dataclasses import dataclass
import re

@dataclass(frozen=True)
class RouteResult:
    context_type: str
    analysis_type: str
    campaign_ids:list[str]

def extract_campaign_ids(question: str) -> list[str]:
    # Matches CMP-2026-004 and legacy C001/c123 formats.
    matches = re.findall(
        r"\b(?:CMP-\d{4}-\d{3}|C\d{3})\b",
        question,
        flags=re.IGNORECASE,
    )
    return [match.upper() for match in matches]

def route_question(question: str) -> RouteResult:
    normalized = question.lower()
    campaign_ids = extract_campaign_ids(question)

    comparison_terms = (
        "compare",
        "versus",
        " vs ",
        "difference",
        "better",
        "highest",
        "lowest",
        "best",
        "worst",
        "most",
    )

    customer_terms = (
        "customer",
        "customers",
        "customer id",
        "who responded",
        "who did not respond",
    )

    segment_terms = (
        "segment",
        "segments",
        "customer segment",
        "audience segment",
        "audience",
        "group",
        "groups",
    )

    insight_terms = (
        "what stands out",
        "key insights",
        "important insights",
        "what should we know",
        "what happened",
        "anything unusual",
        "anything unexpected",
        "opportunities",
        "recommendations",
        "what should we do",
        "takeaways",
    )

    evaluation_terms = {
        "best",
        "worst",
        "highest",
        "lowest",
        "most",
        "least",
        "scale",
        "efficiency",
        "opportunity",
        "recommend",
        "prioritize",
        "delivered",
        "generated",
    }

    has_multiple_campaigns = len(campaign_ids) > 1

    has_comparison_term = any(
        term in normalized
        for term in comparison_terms
    )

    is_comparison = (
            has_multiple_campaigns and
            has_comparison_term)

    has_evaluation_term = any(
        term in normalized
        for term in evaluation_terms
    )

    has_insight_term = any(
        term in normalized
        for term in insight_terms
    )

    is_insight_intent = (
            has_evaluation_term or
            has_insight_term)

    if is_comparison:
        return RouteResult(
            analysis_type="comparison",
            context_type="campaign",
            campaign_ids=campaign_ids,
        )

    if is_insight_intent:
        return RouteResult(
            analysis_type="insight",
            context_type="insight",
            campaign_ids=campaign_ids,
        )

    if any(term in normalized for term in segment_terms):
        return RouteResult(
            analysis_type="segment",
            context_type="segment",
            campaign_ids=campaign_ids,
        )

    if any(term in normalized for term in customer_terms):
        return RouteResult(
            analysis_type="detail",
            context_type="customer_campaign",
            campaign_ids=campaign_ids,
        )

    # if any(term in normalized for term in segment_terms):
    #     return RouteResult(
    #         analysis_type="segment",
    #         context_type="segment",
    #         campaign_ids=campaign_ids,
    #     )

    # return RouteResult(
    #     analysis_type=(
    #         "comparison" if is_comparison else "summary"
    #     ),
    #     context_type="campaign",
    #     campaign_ids=campaign_ids,
    # )

    # if any(term in normalized for term in insight_terms):
    #     return RouteResult(
    #         analysis_type="insight",
    #         context_type="insight",
    #         campaign_ids=campaign_ids,
    #     )

    # if any(term in normalized for term in evaluation_terms):
    #     return RouteResult(
    #         analysis_type="insight",
    #         context_type="insight",
    #         campaign_ids=campaign_ids,
    #     )

    # if any(term in normalized for term in segment_terms):
    #     return RouteResult(
    #         analysis_type=(
    #             "comparison" if is_comparison else "summary"
    #         ),
    #         context_type="segment",
    #         campaign_ids=campaign_ids,
    #     )

    if campaign_ids:
        return RouteResult(
            analysis_type="comparison" ,
            context_type="campaign",
            campaign_ids=campaign_ids,
        )

    # if campaign_ids:
    #     return RouteResult(
    #         analysis_type="insight",
    #         context_type="insight",
    #         campaign_ids=campaign_ids,
    #     )
    #
    # if campaign_ids:
    #     return RouteResult(
    #         analysis_type="summary" ,
    #         context_type="campaign",
    #         campaign_ids=campaign_ids,
    #     )

    return RouteResult(
        analysis_type="summary",
        context_type="campaign",
        campaign_ids=campaign_ids,
    )

