import pandas as pd
from app.config.paths import DATA_DIR

def build_campaign_context(campaign_df, campaign_id: str) -> str:
    campaign_rows = campaign_df[campaign_df["campaign_id"] == campaign_id]
    goal_rows = campaign_goals_df[campaign_goals_df["campaign_id"] == campaign_id]

    if campaign_rows.empty:
        raise ValueError(f"{campaign_id} not found")

    if goal_rows.empty:
        raise ValueError(f"Goal data for {campaign_id} not found")

    campaign_name = campaign_rows["campaign_name"].dropna().unique()

    if len(campaign_name) != 1:
        raise ValueError(
            f"Expected one campaign name for campaign_id={campaign_id}, "
            f"found {len(campaign_name)}"
        )

    campaign_name = campaign_rows['campaign_name'].iloc[0]
    start_date = campaign_rows['start_date'].iloc[0]
    end_date = campaign_rows['end_date'].iloc[0]
    goal_row = goal_rows.iloc[0]

    context_lines = [f"Campaign Name: {campaign_name}",
                     f"Campaign ID: {campaign_id}",
                     f"Start Date: {start_date}",
                     f"End Date: {end_date}\n",
                     "Campaign Metadata\n"
                     f"------------------",
                     f"Campaign Goal: {goal_row['campaign_goal']}",
                     f"Offer: {goal_row['offer']}",
                     f"Channel: {goal_row['channel']}",
                     f"Duration: {goal_row['duration']}",
                     f"Budget: ${goal_row['budget']:,}",
                     f"Target KPI: {goal_row['target_kpi']}",
                     f"Secondary KPI: {goal_row['secondary_kpi']}",
                     f"Audience: {goal_row['audience']}",
                     "",
                     "Segment Performance:\n"
                     f"---------------------",
                     ]

    for _, row in campaign_rows.iterrows():
        context_lines.extend([
            "",
            f"Segment: {row['customer_segment']}\n",
            f"Audience\n"
            f"---------",
            f"Test Audience: {row['test_audience']:,}",
            f"Control Audience: {row['control_audience']:,}\n",
            f"Performance\n"
            f"------------",
            f"Test Conversion Rate: {row['test_conversion_rate']:.1%}",
            f"Control Conversion Rate: {row['control_conversion_rate']:.1%}",
            f"Absolute Lift: {row['absolute_lift']}",
            f"Estimated Incremental Conversions: {row['incremental_conversions']:,}\n",
            f"Financial Impact\n"
            f"-----------------",
            f"Incremental Revenue: ${row['incremental_rev']:,.2f}",
            f"Campaign Cost: ${row['total_cmpgn_cost']:,.2f}",
            f"Marketing ROI: {row['marketing_roi']:.1%}",
        ])

    return "\n".join(context_lines)

file_name="campaign_performance_summary.csv"
campaign_path = DATA_DIR / file_name
campaign_df = pd.read_csv(campaign_path,encoding='utf-8')

goals_file_name = "campaign_goals.csv"
goals_path = DATA_DIR / goals_file_name
campaign_goals_df = pd.read_csv(goals_path, encoding='utf-8')

# print(build_campaign_context(campaign_df,"CMP-2026-003"))