import pandas as pd
from app.config.paths import DATA_DIR
from app.utils.file_utils import load_sql_extracts


extracts = load_sql_extracts(
    [
        "campaign_segment_summary",
        "campaign_summary",
        "analytic_layer",
        "unique_campaigns_list",
    ]
)


unique_campaigns_df = extracts["unique_campaigns_list"]
segment_df = extracts["campaign_segment_summary"]
summary_df = extracts["campaign_summary"]
customer_df = extracts["analytic_layer"]

goals_file_name = "campaign_goals.csv"
goals_path = DATA_DIR / goals_file_name
campaign_goals_df = pd.read_csv(goals_path, encoding='utf-8')

