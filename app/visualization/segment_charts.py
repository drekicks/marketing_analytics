import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from app.config.paths import OUTPUT_DIR
from pathlib import Path
import numpy as np

output = OUTPUT_DIR

def create_segment_conversion_rate_chart(
        segment_df: pd.DataFrame,
        campaign_id: str,
        output_path: Path,
) -> Path:
    """Create and save a segment conversion-rate bar chart."""

    campaign_rows = segment_df.loc[
        segment_df["campaign_id"].astype(str) == str(campaign_id)
    ].copy()

    if campaign_rows.empty:
        raise ValueError(
            f"No segment data found for campaign ID: {campaign_id}"
        )

    required_columns = ["customer_segment", "test_conversion_rate", "control_conversion_rate"]

    if not all(column in campaign_rows.columns for column in required_columns):
        raise ValueError(
            f"Missing required columns in segment data: {required_columns}"
        )

    campaign_rows = campaign_rows.sort_values("test_conversion_rate", ascending=False)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    x = np.arange(len(campaign_rows["customer_segment"]))  # positions for each segment
    width = 0.35  # width of each bar

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.bar(x - width / 2, campaign_rows["test_conversion_rate"], width, label="Test", color="#0072B2")
    ax.bar(x + width / 2, campaign_rows["control_conversion_rate"], width, label="Control", color="#E69F00")

    ax.legend(
        title="Treatment Group",
        loc="upper right",
        fontsize=9,
        frameon=False,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(campaign_rows["customer_segment"].astype(str).tolist())
    ax.set_title(f"Conversion Rate by Customer Segment - {campaign_id}")
    ax.set_xlabel("Customer Segment")
    ax.set_ylabel("Conversion Rate")

    # Format y-axis as percentage
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0%}"))

    # Label each bar with its value
    for i, value in enumerate(campaign_rows["test_conversion_rate"]):
        ax.annotate(
            f"{value:,.0%}",
            xy=(i - width/2, value),
            xytext=(0, 3),
            textcoords="offset points",
            ha="left",
            fontsize=9,
        )

    for i, value in enumerate(campaign_rows["control_conversion_rate"]):
        ax.annotate(
            f"{value:,.0%}",
            xy=(i + width / 2, value),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            fontsize=9,
        )

    fig.tight_layout()
    fig.savefig(
        output_path,
        dpi=150,
        bbox_inches='tight'
    )

    plt.close(fig)

    return output_path

def create_segment_revenue_chart(
        segment_df: pd.DataFrame,
        campaign_id: str,
        output_path: Path,
) -> Path:
    """Create and save a segment conversion-rate bar chart."""

    campaign_rows = segment_df.loc[
        segment_df["campaign_id"].astype(str) == str(campaign_id)
    ].copy()

    if campaign_rows.empty:
        raise ValueError(
            f"No segment data found for campaign ID: {campaign_id}"
        )

    required_columns = ["customer_segment", "campaign_revenue"]

    if not all(column in campaign_rows.columns for column in required_columns):
        raise ValueError(
            f"Missing required columns in segment data: {required_columns}"
        )

    campaign_rows = campaign_rows.sort_values("campaign_revenue", ascending=False)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(campaign_rows["customer_segment"], campaign_rows["campaign_revenue"], color="#009E73")

    ax.set_title(f"Revenue by Customer Segment - {campaign_id}")
    ax.set_xlabel("Customer Segment")
    ax.set_ylabel("Revenue")

    # Format y-axis as percentage
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x:,.0f}"))

    # Label each bar with its value
    for i, value in enumerate(campaign_rows["campaign_revenue"]):
        ax.annotate(
            f"${value:,.0f}",
            xy=(i, value),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            fontsize=9,
        )

    fig.tight_layout()
    fig.savefig(
        output_path,
        dpi=150,
        bbox_inches='tight'
    )

    plt.close(fig)

    return output_path