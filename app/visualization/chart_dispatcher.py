from pathlib import Path
import pandas as pd
from app.config.router import VisualizationRequest
from app.visualization.segment_charts import create_segment_conversion_rate_chart, create_segment_revenue_chart
# from app.config.paths import OUTPUT_DIR

# output = OUTPUT_DIR

def create_visualization(
        request: VisualizationRequest,
        campaign_id: str,
        segment_df: pd.DataFrame,
        output_dir: Path,
) -> Path:

   if(
       request.subject == "segment"
       and request.metric == "conversion_rate"
       and request.chart_type=="bar"
   ):
        return create_segment_conversion_rate_chart(
            segment_df = segment_df,
            campaign_id=campaign_id,
            output_path=output_dir/ "charts"/f"{campaign_id}_segment_conversion_rate.png",
        )

   if (
           request.subject == "segment"
           and request.metric == "revenue"
           and request.chart_type == "bar"
   ):
       return create_segment_revenue_chart(
           segment_df=segment_df,
           campaign_id=campaign_id,
           output_path=output_dir / "charts" / f"{campaign_id}_segment_revenue.png",
       )

   raise ValueError(
       "Unsupported visualization request: "
       f"subject={request.subject}, "
       f"metric={request.metric}, "
       f"chart_type={request.chart_type}"
   )





