"""Chainlit UI helpers (no Chainlit runtime needed)."""

import pandas as pd

from app.services.analyst_service import AnalystResult
from app.ui.chainlit_support import (
    EXAMPLE_QUESTIONS,
    SQL_ELEMENT_NAME,
    campaign_label,
    campaign_options,
    campaign_profiles,
    added_campaigns,
    campaign_switch_note,
    new_campaigns_note,
    picked_campaign,
    format_sql_for_display,
    reply_parts,
    welcome_text,
)
from app.utils.data_loader import get_campaign_data


def test_campaign_options_from_demo_data():
    options = campaign_options(get_campaign_data().unique_campaigns)

    assert options, "demo data should list campaigns"
    campaign_id, label = options[0]
    assert campaign_id.startswith("CMP-")
    assert label.startswith(f"{campaign_id} — ")


def test_campaign_options_strip_and_dedupe_keeping_order():
    frame = pd.DataFrame(
        {
            "campaign_id": [" CMP-2026-004 ", "CMP-2025-002", "CMP-2026-004", ""],
            "campaign_name": ["Spring", "Summer", "Spring again", "Blank"],
        }
    )

    assert campaign_options(frame) == [
        ("CMP-2026-004", "CMP-2026-004 — Spring"),
        ("CMP-2025-002", "CMP-2025-002 — Summer"),
    ]


def test_campaign_label_falls_back_to_id():
    options = [("CMP-2026-004", "CMP-2026-004 — Spring")]

    assert campaign_label(options, "CMP-2026-004") == "CMP-2026-004 — Spring"
    assert campaign_label(options, "CMP-2099-001") == "CMP-2099-001"


def test_welcome_text_names_the_campaign():
    assert "CMP-2026-004 — Spring" in welcome_text("CMP-2026-004 — Spring")


def test_reply_parts_plain_answer():
    parts = reply_parts(AnalystResult(answer="Growth led on lift."))

    assert parts.content == "Growth led on lift."
    assert parts.chart_path is None and parts.sql is None


def test_reply_parts_with_chart_and_sql(tmp_path):
    chart = tmp_path / "chart.png"
    chart.write_bytes(b"png")

    parts = reply_parts(
        AnalystResult(answer="India leads.", chart_path=chart, sql="SELECT 1 FROM cal")
    )

    assert parts.chart_path == str(chart)
    assert parts.sql == "SELECT\n  1\nFROM cal"
    # The side panel only links when its name appears in the message text.
    assert SQL_ELEMENT_NAME in parts.content


def test_reply_parts_skips_missing_chart_file(tmp_path):
    parts = reply_parts(AnalystResult(answer="x", chart_path=tmp_path / "gone.png"))

    assert parts.chart_path is None


def test_examples_match_the_streamlit_sidebar():
    sidebar = open("streamlit_app.py", encoding="utf-8").read()

    for question in EXAMPLE_QUESTIONS:
        assert question in sidebar


def test_format_sql_for_display_only_changes_whitespace():
    raw = "SELECT country, COUNT(*) AS n FROM cal GROUP BY 1 ORDER BY 2 DESC LIMIT 3"

    pretty = format_sql_for_display(raw)

    assert "\n" in pretty
    assert pretty.split() == format_sql_for_display(pretty).split()
    assert " ".join(pretty.split()) == raw


def test_format_sql_for_display_returns_unparseable_text_unchanged():
    assert format_sql_for_display("not sql (((") == "not sql ((("


def test_campaign_profiles_from_demo_data():
    data = get_campaign_data()
    profiles = campaign_profiles(data.unique_campaigns)
    options = campaign_options(data.unique_campaigns)

    assert [(p.campaign_id, p.label) for p in profiles] == options
    assert [p.default for p in profiles] == [True] + [False] * (len(profiles) - 1)
    assert all("Channel:" in p.description for p in profiles)


def test_campaign_profiles_dedupe_and_tolerate_missing_details():
    frame = pd.DataFrame(
        {
            "campaign_id": ["CMP-2026-004", "CMP-2026-004", "CMP-2025-002"],
            "campaign_name": ["Spring", "Spring again", "Summer"],
        }
    )

    profiles = campaign_profiles(frame)

    assert [p.campaign_id for p in profiles] == ["CMP-2026-004", "CMP-2025-002"]
    assert profiles[0].description == "CMP-2026-004 — Spring"


def test_welcome_text_points_to_the_campaign_picker():
    text = welcome_text("CMP-2026-004 — Spring")
    assert "Campaign picker" in text
    assert "Executive summary and Refresh data buttons" in text


def test_picked_campaign_reads_the_message_box_picker():
    valid = {"CMP-2025-002", "CMP-2026-004"}

    assert picked_campaign({"campaign": "CMP-2026-004"}, valid) == "CMP-2026-004"
    assert picked_campaign({"campaign": "CMP-2099-001"}, valid) is None
    assert picked_campaign({}, valid) is None
    assert picked_campaign(None, valid) is None


def test_campaign_switch_note_only_when_the_campaign_changed():
    options = [("CMP-2025-002", "CMP-2025-002 — Summer"), ("CMP-2026-004", "CMP-2026-004 — Spring")]

    assert campaign_switch_note(options, "CMP-2025-002", "CMP-2026-004") == (
        "Active campaign is now CMP-2026-004 — Spring."
    )
    assert campaign_switch_note(options, "CMP-2026-004", "CMP-2026-004") is None
    assert campaign_switch_note(options, "CMP-2026-004", None) is None


def test_welcome_text_shows_the_assistant_name():
    assert welcome_text("CMP-2026-004 — Spring").startswith("## AI Marketing Analytics Assistant\n")


def test_added_campaigns_lists_only_new_ones():
    old = [("CMP-2026-004", "CMP-2026-004 — Spring"), ("CMP-2026-005", "CMP-2026-005 — Fall")]
    new = [("CMP-2026-004", "CMP-2026-004 — Spring"), ("CMP-2026-006", "CMP-2026-006 — Winter")]

    assert added_campaigns(old, new) == [("CMP-2026-006", "CMP-2026-006 — Winter")]
    assert added_campaigns(old, old) == []


def test_new_campaigns_note():
    assert new_campaigns_note([]) is None
    assert new_campaigns_note([("CMP-2026-006", "CMP-2026-006 — Winter")]) == (
        "New campaign available: CMP-2026-006 — Winter. Pick it in the Campaign picker."
    )
    assert "New campaigns available: A, B" in new_campaigns_note([("a", "A"), ("b", "B")])
