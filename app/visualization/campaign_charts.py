import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from app.config.paths import OUTPUT_DIR
from pathlib import Path

output = OUTPUT_DIR

def create_campaign_conversion_rate_chart(
        summary_df: pd.DataFrame,
        output_path: Path,
        campaign_ids: list[str] | None = None,
) -> Path:
    """Create and save a campaign conversion-rate bar chart."""
    chart_data = summary_df.copy()

    if campaign_ids:
        normalized_ids = {
            str(campaign_id).strip()
            for campaign_id in campaign_ids
        }

        chart_data = chart_data.loc[
            chart_data["campaign_id"]
            .astype(str)
            .str.strip()
            .isin(normalized_ids)
        ].copy()

    if chart_data.empty:
        raise ValueError(
            f"No campaign data found for requested chart"
        )

    required_columns = ["campaign_id", "conversion_rate"]

    if not all(column in chart_data.columns for column in required_columns):
        raise ValueError(
            f"Missing required columns in campaign data: {required_columns}"
        )

    campaign_rows = chart_data.sort_values("conversion_rate", ascending=False)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(campaign_rows["campaign_id"], campaign_rows["conversion_rate"], color="#648FFF")

    ax.set_title(f"Conversion Rate by Campaign")
    ax.set_xlabel("Campaign ID")
    ax.set_ylabel("Conversion Rate")

    # Format y-axis as percentage
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0%}"))

    # Label each bar with its value
    for i, value in enumerate(campaign_rows["conversion_rate"]):
        ax.annotate(
            f"{value:,.0%}",
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

def create_campaign_revenue_chart(
        summary_df: pd.DataFrame,
        output_path: Path,
        campaign_ids: list[str] | None = None,
) -> Path:
    """Create and save a campaign revenue bar chart."""
    chart_data = summary_df.copy()

    if campaign_ids:
        normalized_ids = {
            str(campaign_id).strip()
            for campaign_id in campaign_ids
        }

        chart_data = chart_data.loc[
            chart_data["campaign_id"]
            .astype(str)
            .str.strip()
            .isin(normalized_ids)
        ].copy()

    if chart_data.empty:
        raise ValueError(
            f"No campaign data found for requested chart"
        )

    required_columns = ["campaign_id", "campaign_revenue"]

    if not all(column in chart_data.columns for column in required_columns):
        raise ValueError(
            f"Missing required columns in campaign data: {required_columns}"
        )

    campaign_rows = chart_data.sort_values("campaign_revenue", ascending=False)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(campaign_rows["campaign_id"], campaign_rows["campaign_revenue"], color="#D55E00")

    ax.set_title(f"Revenue by Campaign")
    ax.set_xlabel("Campaign ID")
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