import pandas as pd
from app.ai.context_loader import campaign_goals_df

# from app.ai.context_loader import summary_df, segment_df, campaign_goals_df, customer_df

def build_segment_context(campaign_df:pd.DataFrame,
                          goals_df: pd.DataFrame,
                          campaign_id: str
                          ) -> str:
    """
        Grain:
            One row per campaign and segment.

        Used for:
            Segment performance and segment comparisons.
        """
    campaign_rows = campaign_df[campaign_df["campaign_id"] == campaign_id]
    goal_rows = goals_df[campaign_goals_df["campaign_id"] == campaign_id]

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
                     f"Target Audience: {goal_row['audience']}",
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
            f"Campaign Cost: ${row['total_campaign_cost']:,.2f}",
            f"Marketing ROI: {row['marketing_roi']:.1%}",
            f"Campaign Revenue: ${row['campaign_revenue']:,.2f}",
            f"Conversions: {row['campaign_conversions']:,}",
            f"Revenue Per Conversion: ${row['revenue_per_conversion']:.2f}",
        ])

    return "\n".join(context_lines)

def build_campaign_context(summary_df:pd.DataFrame,
                           goals_df: pd.DataFrame,
                           campaign_id: str,) -> str:
    """
        Grain:
            One row per campaign.

        Used for:
            Campaign summaries, rankings, and campaign comparisons.
        """
    campaign_id = str(campaign_id)

    campaign_summary_rows = summary_df[
        summary_df["campaign_id"] == campaign_id
    ]

    goal_rows = goals_df[
        goals_df["campaign_id"] == campaign_id
    ]

    if campaign_summary_rows.empty:
        raise ValueError(f"{campaign_id} not found")

    if goal_rows.empty:
        raise ValueError(f"Goal data for {campaign_id} not found")

    if len(campaign_summary_rows) != 1:
        raise ValueError(
            f"Expected one campaign summary row for "
            f"campaign_id={campaign_id}, "
            f"found {len(campaign_summary_rows)}"
        )

    if len(goal_rows) != 1:
        raise ValueError(
            f"Expected one goal row for campaign_id={campaign_id}, "
            f"found {len(goal_rows)}"
        )

    summary_row = campaign_summary_rows.iloc[0]
    goal_row = goal_rows.iloc[0]

    context_lines = [f"Campaign Name: {summary_row['campaign_name']}",
                     f"Campaign ID: {campaign_id}",
                     f"Start Date: {summary_row['start_date']}",
                     f"End Date: {summary_row['end_date']}",
                     "",
                     "Campaign Metadata\n"
                     f"------------------",
                     f"Campaign Goal: {goal_row['campaign_goal']}",
                     f"Offer: {goal_row['offer']}",
                     f"Channel: {goal_row['channel']}",
                     f"Duration: {goal_row['duration']}",
                     f"Budget: ${goal_row['budget']:,}",
                     f"Target KPI: {goal_row['target_kpi']}",
                     f"Secondary KPI: {goal_row['secondary_kpi']}",
                     f"Target Audience: {goal_row['audience']}",
                     "",
                     "Campaign Performance:\n"
                     f"---------------------",
                     f"Audience Size: {summary_row['audience_size']:,}",
                     f"Campaign Revenue: ${summary_row['campaign_revenue']:,.2f}",
                     f"Campaign Cost: ${summary_row['total_campaign_cost']:,.2f}",
                     f"Conversions: {summary_row['conversions']:,}",
                     f"Revenue Per Customer: ${summary_row['revenue_per_customer']:.2f}",
                     f"Revenue Per Conversion: ${summary_row['revenue_per_conversion']:.2f}",
                     ]
    return "\n".join(context_lines)


def build_campaign_comparison_context(
        summary_df: pd.DataFrame,
        goals_df: pd.DataFrame,
        campaign_ids: list[str],) -> str:
    """Build context for comparing two or more campaigns."""

    if len(campaign_ids) < 2:
        raise ValueError(
            "Campaign comparison requires at least two campaign IDs"
        )

    campaign_contexts = [
        build_campaign_context(
            summary_df=summary_df,
            goals_df=goals_df,
            campaign_id=campaign_id,
        )
        for campaign_id in campaign_ids
    ]

    return "\n\n".join(
        [
            "CAMPAIGN COMPARISON CONTEXT",
            "===========================",
            *campaign_contexts,
        ]
    )


def build_customer_context(customer_df:pd.DataFrame,
                           goals_df: pd.DataFrame,
                           campaign_id: str,) -> str:
    """
       Grain:
           One row per customer and campaign.

       Used for:
           Customer-level targeting and response questions.
       """

    campaign_id = str(campaign_id)

    campaign_customer_rows = customer_df[
        customer_df["campaign_id"] == campaign_id
    ]

    goal_rows = goals_df[
        goals_df["campaign_id"] == campaign_id
    ]

    if campaign_customer_rows.empty:
        raise ValueError(f"{campaign_id} not found")

    if goal_rows.empty:
        raise ValueError(f"Goal data for {campaign_id} not found")

    if len(goal_rows) != 1:
        raise ValueError(
            f"Expected one goal row for campaign_id={campaign_id}, "
            f"found {len(goal_rows)}"
        )

    campaign_name = campaign_customer_rows['campaign_name'].iloc[0]
    start_date = campaign_customer_rows['start_date'].iloc[0]
    end_date = campaign_customer_rows['end_date'].iloc[0]
    goal_row = goal_rows.iloc[0]

    context_lines = [
                     f"Campaign Name: {campaign_name}",
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
                     f"Target Audience: {goal_row['audience']}",
                     "",
                     ]
    for _, row in campaign_customer_rows.iterrows():
        context_lines.extend([
                      "Customer Details\n"
                      f"------------------",
                      f"Customer ID: {row['customer_id']}",
                      f"Customer Tier: {row['customer_tier']}",
                      f"Segment: {row['customer_segment']}",
                      f"Treatment Group: {row['treatment_grp']}",
                      f"Converted: {row['cnvrsn_flg']}",
                      "",
                      "Campaign Performance:\n"
                     f"---------------------",
                     f"Campaign Revenue: ${row['campaign_revenue']:,.2f}",
                     f"Campaign Cost: ${row['total_campaign_cost']:,.2f}\n",
                     ]
        )
    return "\n".join(context_lines)

