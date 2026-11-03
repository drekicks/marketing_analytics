import pandas as pd

from app.ai.insight_signals import calculate_segment_signals, format_segment_signals


def _segment_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "campaign_id": "CMP-2026-001",
                "customer_segment": "A",
                "campaign_conversions": 10,
                "campaign_revenue": 1000.0,
                "absolute_lift": 1.2,
                "segment_revenue_per_conversion": 100.0,
                "segment_conversion_rate": 0.10,
            },
            {
                "campaign_id": "CMP-2026-001",
                "customer_segment": "B",
                "campaign_conversions": 20,
                "campaign_revenue": 900.0,
                "absolute_lift": 1.0,
                "segment_revenue_per_conversion": 45.0,
                "segment_conversion_rate": 0.08,
            },
            {
                "campaign_id": "CMP-2026-002",
                "customer_segment": "Z",
                "campaign_conversions": 22,
                "campaign_revenue": 1800.0,
                "absolute_lift": 2.1,
                "segment_revenue_per_conversion": 120.0,
                "segment_conversion_rate": 0.15,
            },
        ]
    )


def test_calculate_segment_signals_campaign_scope() -> None:
    signals = calculate_segment_signals(_segment_rows(), campaign_id="CMP-2026-001")

    assert signals["highest_conversions"]["segment"] == "B"
    assert signals["highest_revenue"]["segment"] == "A"
    assert signals["highest_revenue_per_conversion"]["segment"] == "A"
    assert signals["lowest_conversion_rate"]["segment"] == "B"


def test_calculate_segment_signals_portfolio_scope_labels_campaign_and_segment() -> None:
    signals = calculate_segment_signals(_segment_rows(), campaign_id=None)

    assert signals["highest_revenue"]["segment"] == "CMP-2026-002 - Z"


def test_format_segment_signals_lists_every_signal() -> None:
    text = format_segment_signals(
        calculate_segment_signals(_segment_rows(), campaign_id="CMP-2026-001")
    )

    assert text.startswith("DERIVED SEGMENT SIGNALS")
    assert "Highest revenue per conversion: A ($100.00)" in text
