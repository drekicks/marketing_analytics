from pathlib import Path
import pandas as pd
from app.config.router import VisualizationRequest
from app.visualization.segment_charts import create_segment_conversion_rate_chart, create_segment_revenue_chart
from app.visualization.campaign_charts import create_campaign_conversion_rate_chart, create_campaign_revenue_chart
# from app.config.paths import OUTPUT_DIR

# output = OUTPUT_DIR

def create_visualization(
        request: VisualizationRequest,
        campaign_id: str,
        segment_df: pd.DataFrame,
        summary_df: pd.DataFrame,
        output_dir: Path,
        campaign_ids: list[str] | None = None,
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

   if (
           request.subject == "campaign"
           and request.metric == "conversion_rate"
           and request.chart_type == "bar"
   ):
       if campaign_ids:
           campaign_label = "_".join(campaign_ids)
           file_name = f"{campaign_label}_campaign_conversion_rate.png"
       else:
           file_name = "all_campaigns_conversion_rate.png"

       return create_campaign_conversion_rate_chart(
           summary_df= summary_df,
           campaign_ids=campaign_ids,
           output_path=output_dir / "charts" / file_name,
       )

   if (
           request.subject == "campaign"
           and request.metric == "revenue"
           and request.chart_type == "bar"
   ):
       if campaign_ids:
           campaign_label = "_".join(campaign_ids)
           file_name = f"{campaign_label}_campaign_revenue.png"
       else:
           file_name = "all_campaigns_revenue.png"

       return create_campaign_revenue_chart(
           summary_df=summary_df,
           campaign_ids=campaign_ids,
           output_path=output_dir / "charts" / file_name,
       )

   raise ValueError(
       "Unsupported visualization request: "
       f"subject={request.subject}, "
       f"metric={request.metric}, "
       f"chart_type={request.chart_type}"
   )





