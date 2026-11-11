import pytest

from app.config.router import VS_PATTERN, route_question


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
        "Across all campaigns, how much has customer ID 7470 spent?",
        "How much has customer 7470 spent?",
        "What did customer #7470 buy across campaigns?",
        "Across all campaigns, which countries had the most converters?",
        "Overall, how many customers converted?",
        "Which customers spent the most across all campaigns?",
        "Who spent the most across all campaigns?",
        "Who are our biggest spenders overall?",
        "Across all campaigns, what is the average spend per customer?",
        "Who converted in the test group?",
        "Top spenders this campaign",
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
        ("What are the key takeaways across all campaigns?", "insight", "insight"),
        ("Across all campaigns, which segment converted best?", "insight", "insight"),
        ("How much did we spend on the campaign?", "campaign", "summary"),
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


@pytest.mark.parametrize(
    ("text", "matches"),
    [
        ("cmp-2026-003 vs cmp-2026-004", True),
        ("how did we do vs. last month", True),
        ("canvas campaign", False),
        ("revsion", False),
    ],
)
def test_vs_matches_only_as_a_whole_word(text, matches):
    assert bool(VS_PATTERN.search(text)) is matches


@pytest.mark.parametrize(
    "question",
    [
        "CMP-2026-003 vs CMP-2026-004",
        "How did we do vs. CMP-2026-003?",
    ],
)
def test_vs_as_a_word_is_still_a_comparison(question):
    route = route_question(question)

    assert route.analysis_type == "comparison"
