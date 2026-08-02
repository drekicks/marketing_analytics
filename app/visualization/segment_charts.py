import pandas as pd

from app.utils.data_loader import segment_df
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from app.config.paths import OUTPUT_DIR
from pathlib import Path

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

    required_columns = ["customer_segment", "segment_conversion_rate"]

    # missing_columns = [col for col in required_columns if col not in campaign_rows.columns]

    if not all(column in campaign_rows.columns for column in required_columns):
        raise ValueError(
            f"Missing required columns in segment data: {required_columns}"
        )

    campaign_rows = campaign_rows.sort_values("segment_conversion_rate", ascending=False)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

# # Aggregate revenue by segment and sort descending
# segment_revenue = (
#     filtered_df.groupby("customer_segment")["campaign_revenue"]
#     .sum()
#     .reset_index()
#     .sort_values("campaign_revenue", ascending=False)
# )

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(campaign_rows["customer_segment"], campaign_rows["segment_conversion_rate"], color="#4C72B0")

    ax.set_title(f"Conversion Rate by Customer Segment - {campaign_id}")
    ax.set_xlabel("Customer Segment")
    ax.set_ylabel("Conversion Rate")

    # Format y-axis as percentage
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0%}"))

    # Label each bar with its value
    for i, value in enumerate(campaign_rows["segment_conversion_rate"]):
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