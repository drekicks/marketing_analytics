import pandas as pd

from app.ai.insight_signals import calculate_segment_signals


def test_calculate_segment_signals_campaign_scope() -> None:
    df = pd.DataFrame(
        [
            {
                "campaign_id": "CMP-2026-001",
                "customer_segment": "A",
                "campaign_conversions": 10,
                "campaign_revenue": 1000.0,
                "absolute_lift": 1.2,
                "segment_rpr": 100.0,
                "segment_conversion_rate": 0.10,
            },
            {
                "campaign_id": "CMP-2026-001",
                "customer_segment": "B",
                "campaign_conversions": 20,
                "campaign_revenue": 900.0,
                "absolute_lift": 1.0,
                "segment_rpr": 45.0,
                "segment_conversion_rate": 0.08,
            },
        ]
    )

    signals = calculate_segment_signals(df, campaign_id="CMP-2026-001")

    assert signals["highest_conversions"]["segment"] == "B"


def test_calculate_segment_signals_portfolio_scope_labels_campaign_and_segment() -> None:
    df = pd.DataFrame(
        [
            {
                "campaign_id": "CMP-2026-001",
                "customer_segment": "A",
                "campaign_conversions": 10,
                "campaign_revenue": 1000.0,
                "absolute_lift": 1.2,
                "segment_rpr": 100.0,
                "segment_conversion_rate": 0.10,
            },
            {
                "campaign_id": "CMP-2026-002",
                "customer_segment": "Z",
                "campaign_conversions": 22,
                "campaign_revenue": 1800.0,
                "absolute_lift": 2.1,
                "segment_rpr": 120.0,
                "segment_conversion_rate": 0.15,
            },
        ]
    )

    signals = calculate_segment_signals(df, campaign_id=None)

    assert signals["highest_revenue"]["segment"] == "CMP-2026-002 - Z"
