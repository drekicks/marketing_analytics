import os
from dataclasses import dataclass

import pandas as pd
from app.config.paths import DEMO_DATA_DIR
from app.utils.file_utils import load_sql_extracts
import streamlit as st


DATA_SOURCE = os.getenv("DATA_SOURCE",
                        "csv",
                        ).strip().lower()

# How long Neon data stays cached. New weekly campaigns appear in a running
# app within this window, or at once via clear_campaign_data_cache().
POSTGRES_CACHE_TTL_SECONDS = 600


@dataclass(frozen=True)
class CampaignData:
    summary: pd.DataFrame
    segment: pd.DataFrame
    goals: pd.DataFrame
    unique_campaigns: pd.DataFrame


@st.cache_data
def load_csv_data() -> tuple[
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

    unique_campaigns = pd.read_csv(
        DEMO_DATA_DIR
        / "unique_campaigns.csv"
    )

    return summary, segment, goals, unique_campaigns


@st.cache_data(ttl=POSTGRES_CACHE_TTL_SECONDS)
def load_postgres_data() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """
    Load application datasets from the dbt marts in PostgreSQL (Neon).

    Every dataset, including campaign goals (a dbt model), comes from the
    schema set by ANALYTICS_SCHEMA. Results are cached for
    POSTGRES_CACHE_TTL_SECONDS so Streamlit reruns don't re-query the database.
    """

    extracts = load_sql_extracts(
        [
            "campaign_segment_summary",
            "campaign_summary",
            "unique_campaigns_list",
            "campaign_goals",
        ]
    )

    unique_campaigns = extracts["unique_campaigns_list"]
    segment = extracts["campaign_segment_summary"]
    summary = extracts["campaign_summary"]
    goals = extracts["campaign_goals"]

    return summary, segment, goals, unique_campaigns


def get_campaign_data() -> CampaignData:
    """
    Return the campaign datasets, loading them if the cache is empty or stale.

    Call this where the data is used (per request), not at import time:
    module-level copies would never refresh in a long-running app, so new
    campaigns written to Neon would not appear until a restart.
    """
    if DATA_SOURCE == "csv":
        loaded = load_csv_data()
    elif DATA_SOURCE == "postgres":
        loaded = load_postgres_data()
    else:
        raise ValueError(
            f"Unsupported DATA_SOURCE: {DATA_SOURCE}. "
            "Use 'postgres' or 'csv'."
        )

    summary, segment, goals, unique_campaigns = loaded
    return CampaignData(
        summary=summary,
        segment=segment,
        goals=goals,
        unique_campaigns=unique_campaigns,
    )


def clear_campaign_data_cache() -> None:
    """Drop cached datasets so the next get_campaign_data() reloads them."""
    load_csv_data.clear()
    load_postgres_data.clear()