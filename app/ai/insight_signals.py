from typing import Any
import pandas as pd
from app.ai.context_loader import segment_df


def calculate_segment_signals(segment_df: pd.DataFrame,
                              campaign_id) -> dict[str, Any]:
    """
    Calculate insights for a given segment of data.

    Args:
        segment_data (pd.DataFrame): The segment of data to calculate insights for.

    Returns:
        dict: A dictionary containing the calculated insights.

    Parameters
    ----------
    segment_df:
        Segment summary data containing one row per
        campaign and segment.
    campaign_id:
        Campaign identifier to analyze.

    Returns
    -------
    dict[str, Any]
        Structured performance signals for the campaign.


    Raises
    ------
    ValueError
        If the campaign has no segment data.

    """
    campaign_id = str(campaign_id).strip()

    campaign_segments = segment_df.loc[
        segment_df["campaign_id"].astype(str).str.strip() == campaign_id
        ].copy()

    if campaign_segments.empty:
        raise ValueError(f"No segment data found for campaign {campaign_id}")

    required_columns = [
        "customer_segment",
        "campaign_conversions",
        "campaign_revenue",
        "absolute_lift",
        "segment_rpr",
        "segment_conversion_rate"
    ]

    missing_columns = [col for col in required_columns if col not in campaign_segments.columns]

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(
            f"Segment signal calculation is missing required columns: "
            f"{missing}"
        )

    highest_conversions = campaign_segments.loc[
        campaign_segments["campaign_conversions"].idxmax()
    ]

    highest_revenue = campaign_segments.loc[
        campaign_segments["campaign_revenue"].idxmax()
    ]

    highest_conversion_rate = campaign_segments.loc[
        campaign_segments["segment_conversion_rate"].idxmax()
    ]

    highest_absolute_lift = campaign_segments.loc[
        campaign_segments["absolute_lift"].idxmax()
    ]

    highest_revenue_per_conversion = campaign_segments.loc[
        campaign_segments["segment_rpr"].idxmax()
    ]

    lowest_conversion_rate = campaign_segments.loc[
        campaign_segments["segment_conversion_rate"].idxmin()
    ]

    return {
        "highest_conversions": {
            "segment": highest_conversions["customer_segment"],
            "value":float(highest_conversions["campaign_conversions"])
            },
        "highest_revenue": {
            "segment": highest_revenue["customer_segment"],
            "value": float(highest_revenue["campaign_revenue"])
        },
        "highest_conversion_rate": {
            "segment":highest_conversion_rate["customer_segment"],
            "value": float(highest_conversion_rate["segment_conversion_rate"])
        },
        "highest_absolute_lift": {
            "segment":highest_absolute_lift["customer_segment"],
            "value":float(highest_absolute_lift["absolute_lift"])
            },
        "highest_revenue_per_conversion": {
            "segment":highest_revenue_per_conversion["customer_segment"],
            "value":float(highest_revenue_per_conversion["segment_rpr"])
            },
        "lowest_conversion_rate": {
            "segment":lowest_conversion_rate["customer_segment"],
            "value":float(lowest_conversion_rate["segment_conversion_rate"])
            },
    }

def format_segment_signals(signals: dict[str, Any]) -> str:
    """Format calculated segment signals for the LLM context."""

    return "\n".join(
        [
            "DERIVED SEGMENT SIGNALS",
            "-----------------------",
            (
                "Most conversions: "
                f"{signals['highest_conversions']['segment']} "
                f"({signals['highest_conversions']['value']:,})"
            ),
            (
                "Most revenue: "
                f"{signals['highest_revenue']['segment']} "
                f"(${signals['highest_revenue']['value']:,.2f})"
            ),
            (
                "Highest conversion rate: "
                f"{signals['highest_conversion_rate']['segment']} "
                f"({signals['highest_conversion_rate']['value']:.1%})"
            ),
            (
                "Highest absolute lift: "
                f"{signals['highest_absolute_lift']['segment']} "
                f"({signals['highest_absolute_lift']['value']:.1f} percentage points)"
            ),
            (
                "Highest revenue per conversion: "
                f"{signals['highest_revenue_per_conversion']['segment']} "
                f"(${signals['highest_revenue_per_conversion']['value']:,.2f})"
            ),
            (
                "Lowest conversion rate: "
                f"{signals['lowest_conversion_rate']['segment']} "
                f"({signals['lowest_conversion_rate']['value']:.1%})"
            ),
        ]
    )
signals = calculate_segment_signals(
    segment_df=segment_df,
    campaign_id="CMP-2026-003",
)


# print(format_segment_signals(signals))