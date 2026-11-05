from dataclasses import dataclass
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

# Words that widen a question to the whole portfolio ("Overall, which ...").
# Single source of truth: also used by analyst_chat and analyst_service.
SCOPE_TERMS = (
    "overall",
    "across all",
    "across campaigns",
    "across segments",
    "portfolio-wide",
    "big picture",
    "holistically",
)

VS_PATTERN = re.compile(r"\bvs\b\.?")


def is_scope_request(question: str) -> bool:
    """True when the question asks about all campaigns rather than one."""
    normalized = question.lower()
    return any(term in normalized for term in SCOPE_TERMS)


def route_question(question: str) -> RouteResult:
    normalized = question.lower()
    campaign_ids = extract_campaign_ids(question)

    comparison_terms = (
        "compare",
        "versus",
        "difference",
        "better",
    )

    comparison_reference_terms = (
        "compare to",
        "compare with",
        "compared to",
        "versus",
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
    # conversion_terms = (
    #     "conversions",
    #     "conversion volume",
    # )

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

    knowledge_terms = (
        "what is",
        "what does",
        "how is",
        "how are",
        "calculated",
        "data product",
        "available in",
        "what are",
        "tell me",
        "what's",
        "what's the",
    )

    performance_terms = (
        "perform",
        "performance",
        "performing",
        "breakdown",
        "trend",
    )

    strong_knowledge_terms = (
        "quality check",
        "quality checks",
        "data quality",
        "business rule",
        "business rules",
        "formula",
        "calculated",
        "definition",
        "define",
        "grain",
        "explain",
    )

    # Attributes that only exist at customer grain (customer_analytic_layer),
    # so these questions are answered with guarded text-to-SQL.
    customer_attribute_terms = (
        "country",
        "countries",
        "high value",
        "medium value",
        "low value",
        "customer tier",
        "tier",
        "recency",
        "lapsed",
        "favorite",
        "favourite",
        "film category",
        "genre",
        "category engagement",
        "converters",
        "win-back vip",
        "win-back growth",
        "win-back reactivation",
        "upsell",
        "engagement growth",
        "customer id",
    )

    # "How many ... customers", "which customers", "top 10 customers", ...
    customer_question_pattern = re.compile(
        r"\b(how many|which|top \d+|list|show)\b.*\bcustomers?\b"
    )

    # Customer behaviour without the word "customer": "Who spent the most?",
    # "biggest spenders", "spend per customer".
    customer_activity_pattern = re.compile(
        r"\bwho\b.*\b(spent|spend|spends|bought|buys|purchased|converted|convert)\b"
        r"|\bspenders?\b"
        r"|\bspend per customer\b"
    )

    # A specific customer: "customer 7470", "customer ID 7470", "customer #7470".
    customer_reference_pattern = re.compile(r"\bcustomer\s*(?:id\s*)?#?\s*\d+\b")

    def is_knowledge_question(question: str) -> bool:
        q = question.lower()

        strong_knowledge_match = any(term in q for term in strong_knowledge_terms)

        if strong_knowledge_match:
            return True

        knowledge_match = any(term in q for term in knowledge_terms)
        performance_match = any(term in q for term in performance_terms)
        evaluation_match = any(term in q for term in evaluation_terms)

        return knowledge_match and not performance_match and not evaluation_match

    has_multiple_campaigns = len(campaign_ids) > 1

    # "vs" only as a whole word, so words such as "canvas" don't count.
    has_vs = bool(VS_PATTERN.search(normalized))

    has_comparison_term = has_vs or any(
        term in normalized
        for term in comparison_terms
    )

    has_comparison_reference_term = has_vs or any(
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

    has_scope_term = is_scope_request(question)

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

    # Customer-grain questions win over broad insight: "Across all campaigns, how much
    # has customer 7470 spent?" needs customer rows, which the insight context lacks.
    has_customer_grain_signal = (
        any(term in normalized for term in customer_attribute_terms)
        or bool(customer_question_pattern.search(normalized))
        or bool(customer_activity_pattern.search(normalized))
    )
    if customer_reference_pattern.search(normalized) or (
        has_scope_term and not has_explicit_insight_term and has_customer_grain_signal
    ):
        return RouteResult(
            analysis_type="detail",
            context_type="customer_campaign",
            campaign_ids=campaign_ids,
        )

    # Broad synthesis request
    if is_broad_insight:
        return RouteResult(
            analysis_type="insight",
            context_type="insight",
            campaign_ids=campaign_ids,
        )

    # RAG questions
    if is_knowledge_question(question):
        return RouteResult(
            context_type="knowledge",
            analysis_type="summary",
            campaign_ids=[],
            visualization_request=None,
        )

    # Customer-level question: needs customer-grain attributes or counts.
    # Checked before segments because words such as "group" ("test group")
    # would otherwise send these to the segment summary.
    has_customer_attribute_term = any(
        term in normalized
        for term in customer_attribute_terms
    )

    if (
        has_customer_attribute_term
        or customer_question_pattern.search(normalized)
        or customer_activity_pattern.search(normalized)
    ):
        return RouteResult(
            analysis_type="detail",
            context_type="customer_campaign",
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