"""
Context builders run against the demo CSVs, whose columns now match the
dbt marts. These guard against KeyErrors from column-name drift.
"""

import pandas as pd
import pytest

from app.ai.context_builder import (
    build_campaign_comparison_context,
    build_campaign_context,
    build_insight_context,
    build_segment_context,
)
from app.config.paths import DEMO_DATA_DIR
from app.utils.data_loader import get_campaign_data

_data = get_campaign_data()
summary_df = _data.summary
segment_df = _data.segment
campaign_goals_df = _data.goals
unique_campaigns_df = _data.unique_campaigns

CAMPAIGN_IDS = sorted(unique_campaigns_df["campaign_id"].astype(str).str.strip())

# Column lists of the dbt marts (marketing_analytics_dbt/models/marts/*.sql).
SEGMENT_MART_COLUMNS = [
    "campaign_id", "campaign_name", "customer_segment", "start_date", "end_date",
    "control_audience", "control_revenue", "control_conversions",
    "control_conversion_rate", "control_revenue_per_customer",
    "test_audience", "test_revenue", "test_conversions", "test_conversion_rate",
    "test_revenue_per_customer", "total_campaign_cost", "offer_cost", "contact_cost",
    "absolute_lift", "expected_revenue", "incremental_revenue", "marketing_roi",
    "incremental_conversions", "campaign_revenue", "campaign_conversions",
    "segment_audience", "segment_revenue_per_conversion", "segment_conversion_rate",
]

CAMPAIGN_MART_COLUMNS = [
    "campaign_id", "campaign_name", "channel", "start_date", "end_date",
    "audience_size", "campaign_revenue", "total_campaign_cost",
    "test_conversion_rate", "control_conversion_rate", "conversions",
    "conversion_rate", "revenue_per_customer", "revenue_per_conversion",
    "absolute_lift",
]


def test_demo_csv_columns_match_dbt_marts():
    segment_csv = pd.read_csv(DEMO_DATA_DIR / "campaign_segment_summary.csv", nrows=0)
    summary_csv = pd.read_csv(DEMO_DATA_DIR / "campaign_summary.csv", nrows=0)

    assert list(segment_csv.columns) == SEGMENT_MART_COLUMNS
    assert list(summary_csv.columns) == CAMPAIGN_MART_COLUMNS


@pytest.mark.parametrize("campaign_id", CAMPAIGN_IDS)
def test_campaign_context(campaign_id):
    context = build_campaign_context(summary_df, campaign_goals_df, campaign_id)

    assert f"Campaign ID: {campaign_id}" in context
    assert "Conversion Rate:" in context


@pytest.mark.parametrize("campaign_id", CAMPAIGN_IDS)
def test_segment_context(campaign_id):
    context = build_segment_context(segment_df, campaign_goals_df, campaign_id)

    assert "Incremental Revenue: $" in context
    assert "Revenue Per Conversion: $" in context


@pytest.mark.parametrize("campaign_id", CAMPAIGN_IDS)
def test_single_campaign_insight_context(campaign_id):
    context = build_insight_context(summary_df, segment_df, campaign_goals_df, campaign_id)

    assert "DERIVED SEGMENT SIGNALS" in context
    assert "Highest revenue per conversion:" in context


def test_portfolio_insight_context():
    context = build_insight_context(summary_df, segment_df, campaign_goals_df, None)

    assert "PORTFOLIO-WIDE SCOPE" in context
    assert f"Campaign Count: {len(CAMPAIGN_IDS)}" in context


def test_comparison_context():
    context = build_campaign_comparison_context(
        summary_df, campaign_goals_df, CAMPAIGN_IDS[:2]
    )

    assert context.startswith("CAMPAIGN COMPARISON CONTEXT")


def test_segment_context_uses_goals_argument():
    # The goals passed in must be used, not the module-level goals table.
    with pytest.raises(ValueError, match="Goal data"):
        build_segment_context(segment_df, campaign_goals_df.iloc[0:0], CAMPAIGN_IDS[0])
