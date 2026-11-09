"""
Framework-free helpers for the Chainlit app (chainlit_app.py).

Kept separate from Chainlit so they can be unit-tested without its runtime.
"""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import sqlglot
from sqlglot.errors import ParseError

from app.services.analyst_service import AnalystResult

# Same examples as the Streamlit sidebar.
EXAMPLE_QUESTIONS = (
    "Which segment performed best?",
    "Compare to CMP-2026-003",
    "What are the key takeaways?",
    "Chart revenue by segment",
    "Which countries had the most converters?",
    "Define customer segments",
    "Explain lapsed customers",
)

# Name of the side panel holding the SQL; Chainlit links to a side element
# when its name appears in the message text.
SQL_ELEMENT_NAME = "SQL used"

# Id of the campaign picker shown in the message box (a Chainlit "mode").
CAMPAIGN_MODE_ID = "campaign"


@dataclass(frozen=True)
class ReplyParts:
    content: str
    chart_path: str | None = None
    sql: str | None = None


def campaign_options(unique_campaigns: pd.DataFrame) -> list[tuple[str, str]]:
    """Return (campaign_id, "ID — name") pairs in the data's order, without duplicates."""
    options: list[tuple[str, str]] = []
    seen: set[str] = set()

    for row in unique_campaigns.itertuples(index=False):
        campaign_id = str(row.campaign_id).strip()
        if not campaign_id or campaign_id in seen:
            continue
        seen.add(campaign_id)
        options.append((campaign_id, f"{campaign_id} — {row.campaign_name}"))

    return options


@dataclass(frozen=True)
class CampaignProfile:
    """One entry of the campaign menu in the Chainlit header."""

    campaign_id: str
    label: str
    description: str
    default: bool = False


def campaign_profiles(unique_campaigns: pd.DataFrame) -> list[CampaignProfile]:
    """Campaign menu entries (same order and labels as campaign_options); the first is the default."""
    details = {}
    for row in unique_campaigns.to_dict("records"):
        campaign_id = str(row.get("campaign_id", "")).strip()
        parts = []
        if row.get("channel"):
            parts.append(f"Channel: {row['channel']}")
        if row.get("campaign_start_date"):
            parts.append(f"Starts: {row['campaign_start_date']}")
        details.setdefault(campaign_id, " · ".join(parts))

    return [
        CampaignProfile(
            campaign_id=campaign_id,
            label=label,
            description=details.get(campaign_id) or label,
            default=index == 0,
        )
        for index, (campaign_id, label) in enumerate(campaign_options(unique_campaigns))
    ]


def campaign_label(options: list[tuple[str, str]], campaign_id: str) -> str:
    """Display label for a campaign id (the id itself if it isn't listed)."""
    return dict(options).get(campaign_id, campaign_id)


# Matches [UI].name in .chainlit/config.toml (Chainlit only shows that in the tab title).
ASSISTANT_NAME = "AI Marketing Analytics Assistant"


def welcome_text(label: str) -> str:
    return (
        f"## {ASSISTANT_NAME}\n\n"
        f"**Active campaign:** {label}\n\n"
        "Ask a question about campaign performance, segments, customers, "
        "comparisons or definitions, or pick one of the examples below. "
        "Change the campaign with the Campaign picker in the message box. "
        "Comparing to another campaign makes it the active one, as in the web app."
    )


def picked_campaign(modes: dict | None, valid_ids: set[str]) -> str | None:
    """The campaign chosen in the message-box picker, if it is a known campaign."""
    campaign_id = (modes or {}).get(CAMPAIGN_MODE_ID)
    return campaign_id if campaign_id in valid_ids else None


def campaign_switch_note(options: list[tuple[str, str]], before: str | None, after: str | None) -> str | None:
    """A line telling the user the active campaign changed (e.g. after a comparison)."""
    if not after or after == before:
        return None
    return f"Active campaign is now {campaign_label(options, after)}."


def format_sql_for_display(sql: str) -> str:
    """Pretty-print SQL over several lines (whitespace only; the query is unchanged)."""
    try:
        return sqlglot.parse_one(sql, read="postgres").sql(dialect="postgres", pretty=True)
    except (ParseError, ValueError):
        return sql


def reply_parts(result: AnalystResult) -> ReplyParts:
    """What to show for one answer: text, an optional chart and optional SQL."""
    chart_path = None
    if result.chart_path and Path(result.chart_path).exists():
        chart_path = str(result.chart_path)

    content = result.answer
    if result.sql:
        content = f"{content}\n\nQuery: {SQL_ELEMENT_NAME}"

    sql = format_sql_for_display(result.sql) if result.sql else None

    return ReplyParts(content=content, chart_path=chart_path, sql=sql)
