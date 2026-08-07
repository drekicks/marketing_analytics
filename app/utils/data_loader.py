import pandas as pd
import os
from app.config.paths import DATA_DIR, DEMO_DATA_DIR
from app.utils.file_utils import load_sql_extracts


DATA_SOURCE = os.getenv("DATA_SOURCE",
                        "postgres",
                        ).strip().lower()



def load_csv_data() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """
       Load the synthetic datasets used by the hosted demo.

       CSV mode allows the application to run without requiring access
       to a locally hosted PostgreSQL database.
       """

    summary = pd.read_csv(
        DEMO_DATA_DIR
        / "campaign_summary.csv"
    )

    segment = pd.read_csv(
        DEMO_DATA_DIR
        / "campaign_segment_summary.csv"
    )

    goals = pd.read_csv(
        DEMO_DATA_DIR
        / "campaign_goals.csv"
    )

    customer = pd.read_csv(
        DEMO_DATA_DIR
        / "campaign_analytic_layer.csv"
    )

    unique_campaigns = pd.read_csv(
        DEMO_DATA_DIR
        / "unique_campaigns.csv"
    )

    return summary, segment, goals, customer, unique_campaigns


def load_postgres_data() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """
    Load application datasets from PostgreSQL for local development.
    Campaign goals are still a csv in local development also
    """

    extracts = load_sql_extracts(
        [
            "campaign_segment_summary",
            "campaign_summary",
            "analytic_layer",
            "unique_campaigns_list",
        ]
    )

    unique_campaigns = extracts["unique_campaigns_list"]
    segment = extracts["campaign_segment_summary"]
    summary = extracts["campaign_summary"]
    customer = extracts["analytic_layer"]

    goals = pd.read_csv(
        DEMO_DATA_DIR
        / "campaign_goals.csv"
    )

    return summary, segment, goals, customer, unique_campaigns



if DATA_SOURCE == "csv":
    summary_df, segment_df, campaign_goals_df, customer_df,unique_campaigns_df = (load_csv_data())

elif DATA_SOURCE == "postgres":
    summary_df, segment_df, campaign_goals_df, customer_df, unique_campaigns_df = (load_postgres_data())

else:
    raise ValueError(
        f"Unsupported DATA_SOURCE: {DATA_SOURCE}. "
        "Use 'postgres' or 'csv'."
    )