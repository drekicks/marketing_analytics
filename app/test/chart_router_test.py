import pytest
from app.config.router import route_question

# visualization = VisualizationRequest
# route = route_question()

@pytest.mark.parametrize(
    (
        "question",
        "expected_context",
        "expected_metric",
    ),
    [
        (
            "Chart conversion rate by segment.",
            "segment",
            "conversion_rate",
        ),
        (
            "Graph segment revenue.",
            "segment",
            "revenue",
        ),
        (
            "Plot campaign revenue.",
            "campaign",
            "revenue",
        ),
        (
            "Visualize campaign conversions.",
            "campaign",
            "conversions",
        ),
        (
            "Show me a chart by segment.",
            "segment",
            "conversion_rate",
        ),
    ],
)
def test_visualization_routes(
    question,
    expected_context,
    expected_metric,
):
    route = route_question(question)

    assert route.analysis_type == "visualization"
    assert route.context_type == expected_context
    assert route.visualization_request is not None
    assert route.visualization_request.metric == expected_metric
    assert route.visualization_request.chart_type == "bar"