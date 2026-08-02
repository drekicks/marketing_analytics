import pandas as pd

from app.config.paths import OUTPUT_DIR
from app.utils.data_loader import segment_df
from app.config.router import VisualizationRequest
from app.visualization.chart_dispatcher import (
    create_visualization,
)

output = OUTPUT_DIR

def build_visualization_context(
        request: VisualizationRequest,
        campaign_id: str,
        segment_df: pd.DataFrame,
) -> str:
    if(
        request.subject == "segment"
        and request.metric=="conversion_rate"
    ):
        rows = segment_df.loc[segment_df["campaign_id"].astype(str) == campaign_id].copy()

        if rows.empty:
            raise ValueError(f"No data found for campaign ID {campaign_id}.")

        rows = rows.sort_values("segment_conversion_rate", ascending=False,)

        context_lines = [
            "VISUALIZATION DATA",
            f"Campaign ID: {campaign_id}",
            "Metric: Conversion Rate by Segment",
            "",
        ]

        for _, row in rows.iterrows():
            context_lines.append(
                f"{row['customer_segment']}: "
                f"{row['segment_conversion_rate']:.1%}"
            )

        return "\n".join(context_lines)

    raise ValueError(f"Invalid visualization request: {request}")
