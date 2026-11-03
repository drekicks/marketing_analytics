import pytest

from app.config.router import route_question


@pytest.mark.parametrize(
    "question",
    [
        "How many High Value customers converted in the test group?",
        "Which countries had the most converters?",
        "Which customers responded to the campaign?",
        "How many customers in Canada converted?",
        "What share of lapsed customers converted in the test group vs control?",
        "Which favorite film category had the highest conversion rate?",
        "How many champion customers spent more than $10?",
        "Top 10 customers by campaign revenue",
        "How many customers did we contact?",
        "Compare conversion rate by customer tier",
    ],
)
def test_customer_level_questions_route_to_customer_sql(question):
    route = route_question(question)

    assert route.context_type == "customer_campaign"


@pytest.mark.parametrize(
    ("question", "context_type", "analysis_type"),
    [
        ("Which segment performed best?", "segment", "evaluation"),
        ("Which segment had the highest conversion rate?", "segment", "evaluation"),
        ("Overall, which segment had the highest revenue?", "insight", "insight"),
        ("What are the key takeaways?", "insight", "insight"),
        ("Chart revenue by segment", "segment", "visualization"),
        ("Plot campaign conversion rate", "campaign", "visualization"),
        ("What does Churn Watchlist mean?", "knowledge", "summary"),
        ("Explain lapsed customers", "knowledge", "summary"),
        ("How are customer tiers defined?", "knowledge", "summary"),
        ("Compare to CMP-2026-003", "campaign", "comparison"),
        ("How did the campaign perform?", "campaign", "summary"),
        ("Should this campaign be scaled?", "campaign", "campaign"),
    ],
)
def test_existing_question_types_keep_their_route(question, context_type, analysis_type):
    route = route_question(question)

    assert (route.context_type, route.analysis_type) == (context_type, analysis_type)
