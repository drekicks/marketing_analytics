from datetime import datetime
from pathlib import Path

import streamlit as st

from app.ui.errors import user_message

st.set_page_config(page_title="AI Marketing Analytics Assistant",
                   page_icon="📊",
                   layout="wide")

# -------------------------------------------------------------------
# START-UP
#
# Importing the app validates settings; campaign data (from Neon in postgres
# mode) is loaded on every rerun through a short-lived cache, so new weekly
# campaigns appear without restarting the app. Show a readable message
# instead of a traceback if either fails; reloading the page retries,
# because failed loads aren't cached.
# -------------------------------------------------------------------

try:
    from app.utils.data_loader import clear_campaign_data_cache, get_campaign_data
    from app.services.summary_service import generate_executive_summary
    from app.config.settings import SessionState
    from app.services.analyst_service import process_analyst_question

    campaign_data = get_campaign_data()
except Exception as startup_error:
    st.title("AI Marketing Analytics Assistant")
    st.error(f"The app couldn't start. {user_message(startup_error)}")
    st.stop()

summary_df = campaign_data.summary
campaign_goals_df = campaign_data.goals
unique_campaigns_df = campaign_data.unique_campaigns

# -------------------------------------------------------------------
# PAGE HEADER
# -------------------------------------------------------------------

st.title("AI Marketing Analytics Assistant")

st.write(
    "Explore campaign performance, compare audiences, "
    "and generate AI-assisted insights."
)

# -------------------------------------------------------------------
# SESSION-STATE INITIALIZATION
#
# Streamlit reruns this entire file whenever a user interacts with
# the page. Session state preserves values between those reruns.
# -------------------------------------------------------------------

if "analytics_session" not in st.session_state:
    # Reuse the application's existing session-state model so the
    # Streamlit interface follows the same campaign-context rules
    # as the CLI application.
    st.session_state.analytics_session = SessionState()

if "executive_summary" not in st.session_state:
    # None means no summary has been generated for the active campaign.
    st.session_state.executive_summary = None

if "messages" not in st.session_state:
    # Stores the visible Ask Analyst conversation.
    st.session_state.messages = []

if "analyst_history" not in st.session_state:
    # Ask Analyst format: completed question/answer exchanges.
    st.session_state.analyst_history = []


analytics_session = st.session_state.analytics_session

def handle_campaign_change() -> None:
    """
    Update the active analytics campaign only when the user manually
    changes the Streamlit campaign selector.

    Manual campaign changes start a new analysis session, so outputs
    associated with the previous campaign are cleared.
    """

    selected_display = st.session_state.campaign_selector

    selected_row = campaign_options.loc[
        campaign_options["display_name"] == selected_display
    ].iloc[0]

    new_campaign_id = str(
        selected_row["campaign_id"]
    ).strip()

    # Synchronize the application's reusable session object with
    # the campaign manually selected in the UI.
    st.session_state.analytics_session.active_campaign_id = (
        new_campaign_id
    )

    # Clear content created for the previously selected campaign.
    st.session_state.executive_summary = None
    st.session_state.messages = []
    st.session_state.analyst_history = []


# -------------------------------------------------------------------
# CAMPAIGN OPTIONS
#
# Create a user-friendly label that combines the campaign ID and name.
# This DataFrame is used by both the selector and its change callback.
# -------------------------------------------------------------------

campaign_options = unique_campaigns_df[["campaign_id", "campaign_name"]].copy()

campaign_options['display_name'] = (
        campaign_options['campaign_id'].astype(str)
        + ' - '
        + campaign_options['campaign_name'].astype(str)
)

# -------------------------------------------------------------------
# ACTIVE CAMPAIGN INITIALIZATION
#
# Set the first available campaign as the default only when the
# analytics session does not already have an active campaign.
# -------------------------------------------------------------------

if analytics_session.active_campaign_id is None:
    first_campaign_id = str(
        campaign_options.iloc[0]["campaign_id"]
    ).strip()

    analytics_session.active_campaign_id = first_campaign_id


# -------------------------------------------------------------------
# SELECTOR INITIALIZATION
#
# Streamlit uses the value stored under "campaign_selector" to decide
# which option appears in the dropdown when the page reruns.
# -------------------------------------------------------------------

if "campaign_selector" not in st.session_state:
    active_campaign_row = campaign_options.loc[
        campaign_options["campaign_id"]
        .astype(str)
        .str.strip()
        == str(analytics_session.active_campaign_id).strip()
    ]

    if active_campaign_row.empty:
        st.session_state.campaign_selector = (
            campaign_options.iloc[0]["display_name"]
        )
    else:
        st.session_state.campaign_selector = (
            active_campaign_row.iloc[0]["display_name"]
        )

selected_campaign_id = analytics_session.active_campaign_id
# -------------------------------------------------------------------
# SIDEBAR — CAMPAIGN CONTROLS
# -------------------------------------------------------------------

with st.sidebar:
    st.header("Campaign")

    selected_display_name = st.selectbox(
        "Select a campaign",
        options=campaign_options["display_name"].to_list(),
        key="campaign_selector",
        on_change=handle_campaign_change,
    )

    st.caption("Active Campaign")

    active_row = campaign_options.loc[
        campaign_options["campaign_id"]
        .astype(str)
        .str.strip()
        == str(analytics_session.active_campaign_id).strip()
        ].iloc[0]

    st.success(
        f"{active_row['campaign_id']} — "
        f"{active_row['campaign_name']}"
    )
    # st.success(
    #     f"{analytics_session.active_campaign_id}"
    # )

    st.divider()

    if st.button(
            "Clear Conversation",
            use_container_width=True,
    ):
        st.session_state.messages = []
        st.session_state.analyst_history = []
        st.rerun()

    if st.button(
            "Refresh Data",
            use_container_width=True,
            help="Reload campaigns from the database (e.g. after the weekly campaign run).",
    ):
        clear_campaign_data_cache()
        st.rerun()

    st.divider()

    st.subheader("Example Questions")

    st.markdown("""
        - Which segment performed best?
        - Compare to CMP-2026-003
        - What are the key takeaways?
        - Chart revenue by segment.
        - Which countries had the most converters?
        - Define customer segments.
        - Explain lapsed customers.
        """)

    st.divider()

    st.caption("Portfolio demonstration using synthetic campaign data")

# -------------------------------------------------------------------
# EXECUTIVE SUMMARY
# -------------------------------------------------------------------

if st.button("Generate Executive Summary"):
    with st.spinner("Generating Executive Summary..."):
        try:
            # Same summary as typing "Generate executive summary" in the chat.
            analysis = generate_executive_summary(selected_campaign_id)

            # Save the result so it remains visible after Streamlit reruns.
            st.session_state.executive_summary = analysis

        except Exception as error:
            # Business/data errors show their own message; AI, database and
            # unexpected errors get a friendly message (details are logged).
            st.error(f"Analyst: {user_message(error)}")

st.header("Executive Summary")

# Display the saved summary, or instructions when no summary exists.
if st.session_state.executive_summary:
    st.markdown(st.session_state.executive_summary)

# -------------------------------------------------------------------
# ASK ANALYST — CHAT SHELL
#
# This currently proves that chat messages can be entered, displayed,
# and retained. The real router and analyst workflow will be connected
# in the next phase.
# -------------------------------------------------------------------

st.divider()
st.header("Ask Analyst")

st.write(
    "Ask about campaign performance, segments, comparisons, "
    "portfolio insights, or visualizations."
)

# Rebuild the visible conversation from saved session-state messages.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Re-display charts from earlier answers; otherwise they disappear
        # on every rerun. User messages have no chart_path key.
        chart_path = message.get("chart_path")

        if chart_path and Path(chart_path).exists():
            st.image(chart_path)

        # Customer-level answers come from model-written SQL; show it.
        if message.get("sql"):
            with st.expander("SQL used"):
                st.code(message["sql"], language="sql")

question = st.chat_input(
    "Ask a business question about campaign performance..."
)

if question:
    # Save and immediately display the user's submitted question.
    user_chat_message = {
        "role": "user",
        "content": question,
    }

    st.session_state.messages.append(user_chat_message)

    with st.chat_message("user"):
        st.markdown(question)

    valid_campaign_ids = {
        str(campaign).strip()
        for campaign in unique_campaigns_df["campaign_id"].dropna().tolist()
    }

    try:
        result=process_analyst_question(
            question=question,
            session_state=analytics_session,
            default_campaign_id=selected_campaign_id,
            valid_campaign_ids=valid_campaign_ids,
            conversation_history=st.session_state.analyst_history,
        )

        # Save the completed exchange in the format expected by ask_analyst().
        st.session_state.analyst_history.append(
            {
                "question": question,
                "answer": result.answer,
                "timestamp": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }
        )

        assistant_message= {
            "role": "assistant",
            "content": result.answer,
            "chart_path": (
                str(result.chart_path)
                if result.chart_path else None
            ),
            "sql": result.sql,
        }

    except Exception as error:
        assistant_message = {
            "role": "assistant",
            "content": f"Analyst: {user_message(error)}",
            "chart_path": None,
            "sql": None,
        }

    st.session_state.messages.append(assistant_message)

    with st.chat_message("assistant"):
        st.markdown(assistant_message["content"])

        if assistant_message["chart_path"]:
            st.image(assistant_message["chart_path"])

        if assistant_message["sql"]:
            with st.expander("SQL used"):
                st.code(assistant_message["sql"], language="sql")

