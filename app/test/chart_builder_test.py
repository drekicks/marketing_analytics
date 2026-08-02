from pathlib import Path
from app.config.paths import OUTPUT_DIR
#
# from app.utils.data_loader import segment_df
# from app.visualization.segment_charts import (
#     create_segment_conversion_rate_chart,
# )
# output = OUTPUT_DIR
#
# chart_path = create_segment_conversion_rate_chart(
#     segment_df=segment_df,
#     campaign_id="CMP-2026-003",
#     output_path=output / "charts" / "CMP-2026-003_segment_conversion_rate2.png"
#     )
#
# print(f"Chart created: {chart_path}")


# output_path = output / "charts" / "CMP-2026-003_segment_conversion_rate.png"

from pathlib import Path
from app.config.paths import OUTPUT_DIR
from app.utils.data_loader import segment_df
from app.config.router import VisualizationRequest
from app.visualization.chart_dispatcher import (
    create_visualization,
)

output = OUTPUT_DIR

request = VisualizationRequest(
    subject="segment",
    metric="revenue",
    chart_type="bar",
)

chart_path = create_visualization(
    request=request,
    campaign_id="CMP-2025-002",
    segment_df=segment_df,
    output_dir=output
)

chart_name = f"{request.subject.title()} {request.metric.title()} -"
print(chart_name)
print(f"Saved to: {chart_path}")