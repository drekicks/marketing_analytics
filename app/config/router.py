from dataclasses import dataclass
# from app.config.settings import VisualizationRequest
import re

@dataclass(frozen=True)
class VisualizationRequest:
    subject: str
    metric: str
    chart_type: str = "bar"

@dataclass(frozen=True)
class RouteResult:
    context_type: str
    analysis_type: str
    campaign_ids:list[str]
    visualization_request: VisualizationRequest | None = None

def extract_campaign_ids(question: str) -> list[str]:
    # Matches CMP-2026-004 and legacy C001/c123 formats.
    matches = re.findall(
        r"\bCMP-\d+(?:-\d+)*\b",
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

    comparison_reference_terms = (
        "compare to",
        "compare with",
        "compared to",
        "versus",
        "vs"
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

    visual_terms = (
        "chart",
        "plot",
        "graph",
        "visualize",
        "visualization",
        "diagram",
    )

    revenue_terms = (
        "revenue",
        "sales",
    )

    conversion_rate_terms = (
        "conversion rate",
        "conversion rates",
    )
    # demo mode doesn't have conversions...will add later
    conversion_terms = (
        "conversions",
        "conversion volume",
    )

    pie_terms = (
        "pie",
        "pie chart",
        "pie plot",
        "pie diagram",
    )

    scatter_terms = (
        "scatter",
        "scatter plot",
        "scatter diagram",
    )

    line_term = (
        "line",
        "line chart",
        "line plot",
        "line diagram",
    )


    has_multiple_campaigns = len(campaign_ids) > 1

    has_comparison_term = any(
        term in normalized
        for term in comparison_terms
    )

    has_comparison_reference_term = any(
        term in normalized
        for term in comparison_reference_terms
    )

    has_customer_term = any(
        term in normalized
        for term in customer_terms
    )

    has_visualization_term = any(
        term in normalized
        for term in visual_terms
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

    has_revenue_term = any(
        term in normalized for term in revenue_terms
    )

    has_conversion_rate_term = any(
        term in normalized for term in conversion_rate_terms
    )

# demo mode doesn't have conversions...will add later
#     has_conversion_term = any(
#         term in normalized for term in conversion_terms
#     )

    has_pie_term = any(
        term in normalized for term in pie_terms
    )

    has_scatter_term = any(
        term in normalized for term in scatter_terms
    )

    has_line_term = any(
        term in normalized for term in line_term
    )

    # Explicit multi-campaign comparison
    if has_multiple_campaigns and has_comparison_term:
        return RouteResult(
            analysis_type="comparison",
            context_type="campaign",
            campaign_ids=campaign_ids,
        )

    # Conversational comparison containing one campaign ID.
    # The comparison resolver will combine it with the active campaign.
    if (
            len(campaign_ids) == 1
            and has_comparison_reference_term
    ):
        return RouteResult(
            analysis_type="comparison",
            context_type="campaign",
            campaign_ids=campaign_ids,
        )

    # Visualization request
    # setting default chart type to bar as it is only one supported in v1
    chart_type = "bar"

    if has_pie_term:
        chart_type = "pie"

    if has_line_term:
        chart_type = "line"

    if has_scatter_term:
        chart_type = "scatter"

    if has_visualization_term:
        subject = "segment" if has_segment_term else "campaign"

        if has_revenue_term:
            metric = "revenue"
        elif has_conversion_rate_term:
            metric = "conversion_rate"
        # elif has_conversion_term:
        #     metric = "conversions"
        else:
            raise ValueError(
                "Available charts are campaign or segment revenue "
                "and conversion rate."
            )

        if chart_type != "bar":
            raise ValueError(
                f"{chart_type} is not currently supported. "
                "Available charts are campaign or segment revenue "
                "and conversion rate bar charts."
            )

        return RouteResult(
            analysis_type="visualization",
            context_type=subject,
            campaign_ids=campaign_ids,
            visualization_request=VisualizationRequest(
                subject=subject,
                metric=metric,
                chart_type="bar"
            ),
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
