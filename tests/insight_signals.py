from typing import Any
import pandas as pd
from app.utils.data_loader import segment_df, summary_df


def calculate_segment_signals(
    segment_df: pd.DataFrame,
    campaign_id: str | None = None,
) -> dict[str, Any]:
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
    campaign_label_column = "customer_segment"

    if campaign_id is None:
        campaign_segments = segment_df.copy()
        campaign_segments["campaign_id"] = (
            campaign_segments["campaign_id"].astype(str).str.strip()
        )
        campaign_segments["customer_segment"] = (
            campaign_segments["campaign_id"]
            + " - "
            + campaign_segments["customer_segment"].astype(str)
        )
    else:
        campaign_id = str(campaign_id).strip()
        campaign_segments = segment_df.loc[
            segment_df["campaign_id"].astype(str).str.strip() == campaign_id
        ].copy()

    if campaign_segments.empty:
        if campaign_id is None:
            raise ValueError("No segment data found across campaigns.")
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
            "segment": highest_conversions[campaign_label_column],
            "value":float(highest_conversions["campaign_conversions"])
            },
        "highest_revenue": {
            "segment": highest_revenue[campaign_label_column],
            "value": float(highest_revenue["campaign_revenue"])
        },
        "highest_conversion_rate": {
            "segment":highest_conversion_rate[campaign_label_column],
            "value": float(highest_conversion_rate["segment_conversion_rate"])
        },
        "highest_absolute_lift": {
            "segment":highest_absolute_lift[campaign_label_column],
            "value":float(highest_absolute_lift["absolute_lift"])
            },
        "highest_revenue_per_conversion": {
            "segment":highest_revenue_per_conversion[campaign_label_column],
            "value":float(highest_revenue_per_conversion["segment_rpr"])
            },
        "lowest_conversion_rate": {
            "segment":lowest_conversion_rate[campaign_label_column],
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
    segment_df=segment_df
)

def calculate_campaign_signals(
    summary_df: pd.DataFrame,
    campaign_id: str | None = None,
) -> dict[str, Any]:
    """
    Calculate insights for a given segment of data.

    Args:
        campaign_data (pd.DataFrame): The segment of data to calculate insights for.

    Returns:
        dict: A dictionary containing the calculated insights.

    Parameters
    ----------
    summary_df:
        Summary data containing one row per
        campaign.
    campaign_id:
        Campaign identifier to analyze.

    Returns
    -------
    dict[str, Any]
        Structured performance signals for the campaign.


    Raises
    ------
    ValueError
        If the campaign has no data.

    """
    campaign_label_column = "campaign_name"

    if campaign_id is None:
        campaign = summary_df.copy() #fix
        campaign["campaign_id"] = (
            campaign["campaign_id"].astype(str).str.strip()
        )
        campaign["campaign_name"] = (
            campaign["campaign_id"]
            + " - "
            + campaign["campaign_name"].astype(str)
        )
    else:
        campaign_id = str(campaign_id).strip()
        campaign = summary_df.loc[
            summary_df["campaign_id"].astype(str).str.strip() == campaign_id
        ].copy()

    if campaign.empty:
        if campaign_id is None:
            raise ValueError("No segment data found across campaigns.")
        raise ValueError(f"No segment data found for campaign {campaign_id}")

    required_columns = [
        "campaign_name",
        "conversions",
        "campaign_revenue",
        "absolute_lift",
        "revenue_per_conversion",
        "conversion_rate"
    ]

    missing_columns = [col for col in required_columns if col not in campaign.columns]

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(
            f"Segment signal calculation is missing required columns: "
            f"{missing}"
        )

    highest_conversions = campaign.loc[
        campaign["conversions"].idxmax()
    ]

    highest_revenue = campaign.loc[
        campaign["campaign_revenue"].idxmax()
    ]

    highest_conversion_rate = campaign.loc[
        campaign["conversion_rate"].idxmax()
    ]

    highest_absolute_lift = campaign.loc[
        campaign["absolute_lift"].idxmax()
    ]

    highest_revenue_per_conversion = campaign.loc[
        campaign["revenue_per_conversion"].idxmax()
    ]

    lowest_conversion_rate = campaign.loc[
        campaign["conversion_rate"].idxmin()
    ]

    return {
        "highest_conversions": {
            "campaign": highest_conversions[campaign_label_column],
            "value":float(highest_conversions["conversions"])
            },
        "highest_revenue": {
            "campaign": highest_revenue[campaign_label_column],
            "value": float(highest_revenue["campaign_revenue"])
        },
        "highest_conversion_rate": {
            "campaign":highest_conversion_rate[campaign_label_column],
            "value": float(highest_conversion_rate["conversion_rate"])
        },
        "highest_absolute_lift": {
            "campaign":highest_absolute_lift[campaign_label_column],
            "value":float(highest_absolute_lift["absolute_lift"])
            },
        "highest_revenue_per_conversion": {
            "campaign":highest_revenue_per_conversion[campaign_label_column],
            "value":float(highest_revenue_per_conversion["revenue_per_conversion"])
            },
        "lowest_conversion_rate": {
            "campaign":lowest_conversion_rate[campaign_label_column],
            "value":float(lowest_conversion_rate["conversion_rate"])
            },
    }

def format_campaign_signals(signals: dict[str, Any]) -> str:
    """Format calculated segment signals for the LLM context."""

    return "\n".join(
        [
            "DERIVED CAMPAIGN SIGNALS",
            "-----------------------",
            (
                "Most conversions: "
                f"{signals['highest_conversions']['campaign']} "
                f"({signals['highest_conversions']['value']:,})"
            ),
            (
                "Most revenue: "
                f"{signals['highest_revenue']['campaign']} "
                f"(${signals['highest_revenue']['value']:,.2f})"
            ),
            (
                "Highest conversion rate: "
                f"{signals['highest_conversion_rate']['campaign']} "
                f"({signals['highest_conversion_rate']['value']:.1%})"
            ),
            (
                "Highest absolute lift: "
                f"{signals['highest_absolute_lift']['campaign']} "
                f"({signals['highest_absolute_lift']['value']:.1f} percentage points)"
            ),
            (
                "Highest revenue per conversion: "
                f"{signals['highest_revenue_per_conversion']['campaign']} "
                f"(${signals['highest_revenue_per_conversion']['value']:,.2f})"
            ),
            (
                "Lowest conversion rate: "
                f"{signals['lowest_conversion_rate']['campaign']} "
                f"({signals['lowest_conversion_rate']['value']:.1%})"
            ),
        ]
    )
# signals=calculate_campaign_signals(summary_df)
# ssignals=calculate_segment_signals(segment_df=segment_df)
#
# print(f"{format_campaign_signals(signals)}\n")
# print(format_segment_signals(ssignals))