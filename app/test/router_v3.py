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

    evaluation_terms = (
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
    )

    scope_terms = (
        "overall",
        "across all",
        "across campaigns",
        "across segments",
        "portfolio-wide",
        "big picture",
        "holistically",
    )

    has_multiple_campaigns = len(campaign_ids) > 1

    has_comparison_term = any(
        term in normalized
        for term in comparison_terms
    )

    has_customer_term = any(
        term in normalized
        for term in customer_terms
    )

    has_segment_term = any(
        term in normalized
        for term in segment_terms
    )

    has_evaluation_term = any(
        term in normalized
        for term in evaluation_terms
    )

    has_scope_term = any(
        term in normalized
        for term in scope_terms
    )

    has_explicit_insight_term = any(
        term in normalized
        for term in insight_terms
    )

    is_broad_insight = (
            has_scope_term
            or has_explicit_insight_term
    )

    # Explicit multi-campaign comparison
    if has_multiple_campaigns and has_comparison_term:
        return RouteResult(
            analysis_type="comparison",
            context_type="campaign",
            campaign_ids=campaign_ids,
        )
    # Broad synthesis request
    if is_broad_insight:
        return RouteResult(
            analysis_type="insight",
            context_type="insight",
            campaign_ids=campaign_ids,
        )

    # Explicit segment subject.
    if has_segment_term:
        return RouteResult(
            analysis_type=(
                "evaluation"
                if has_evaluation_term
                else "summary"
            ),
            context_type="segment",
            campaign_ids=campaign_ids,
        )

    # Explicit customer subject.
    if has_customer_term:
        return RouteResult(
            analysis_type="detail",
            context_type="customer_campaign",
            campaign_ids=campaign_ids,
        )

    # Campaign-level evaluation
    if has_evaluation_term:
        return RouteResult(
            analysis_type="campaign",
            context_type="campaign",
            campaign_ids=campaign_ids,
        )

    if campaign_ids:
        return RouteResult(
            analysis_type="comparison",
            context_type="campaign",
            campaign_ids=campaign_ids,
        )

    return RouteResult(
        analysis_type="summary",
        context_type="campaign",
        campaign_ids=campaign_ids,
    )

