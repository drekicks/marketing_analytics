import os
import threading
import time
from dataclasses import dataclass

import pandas as pd
from app.config.paths import DEMO_DATA_DIR
from app.utils.file_utils import load_sql_extracts


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


def load_postgres_data() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """
    Load application datasets from the dbt marts in PostgreSQL (Neon).

    Every dataset, including campaign goals (a dbt model), comes from the
    schema set by ANALYTICS_SCHEMA. get_campaign_data() caches the result for
    POSTGRES_CACHE_TTL_SECONDS so each question doesn't re-query the database.
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


# In-process cache shared by every UI (Streamlit, Chainlit, CLI) and every
# user session in this process. Framework-neutral on purpose: the back end
# must not depend on one UI's caching. Failed loads are never cached.
_cache_lock = threading.Lock()
_cache: dict = {"source": None, "data": None, "loaded_at": 0.0}


def _cache_is_fresh(source: str) -> bool:
    if _cache["data"] is None or _cache["source"] != source:
        return False
    if source == "csv":
        return True
    return time.monotonic() - _cache["loaded_at"] < POSTGRES_CACHE_TTL_SECONDS


def get_campaign_data() -> CampaignData:
    """
    Return the campaign datasets, loading them if the cache is empty or stale.

    Call this where the data is used (per request), not at import time:
    module-level copies would never refresh in a long-running app, so new
    campaigns written to Neon would not appear until a restart.
    """
    source = DATA_SOURCE

    if source not in ("csv", "postgres"):
        raise ValueError(
            f"Unsupported DATA_SOURCE: {source}. "
            "Use 'postgres' or 'csv'."
        )

    with _cache_lock:
        if _cache_is_fresh(source):
            return _cache["data"]

        loaded = load_csv_data() if source == "csv" else load_postgres_data()

        summary, segment, goals, unique_campaigns = loaded
        data = CampaignData(
            summary=summary,
            segment=segment,
            goals=goals,
            unique_campaigns=unique_campaigns,
        )
        _cache.update(source=source, data=data, loaded_at=time.monotonic())
        return data


def clear_campaign_data_cache() -> None:
    """Drop cached datasets so the next get_campaign_data() reloads them."""
    with _cache_lock:
        _cache.update(source=None, data=None, loaded_at=0.0)
