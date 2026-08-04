import streamlit as st
from app.utils.data_loader import campaign_goals_df, summary_df,segment_df, unique_campaigns_df
from app.ai.context_builder import build_campaign_context,build_campaign_comparison_context,build_insight_context
from app.ai.prompt_builder import build_prompt
from app.ai.prompt_loader import load_prompt
from app.ai.llm_client_api import generate_analysis
from app.config.settings import SessionState


st.set_page_config(page_title="AI Marketing Analytics Assistant",
                   page_icon="📊",
                   layout="wide")

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

analytics_session = st.session_state.analytics_session

# -------------------------------------------------------------------
# CAMPAIGN SELECTOR
# -------------------------------------------------------------------

# Create a user-friendly label containing both campaign ID and name.
campaign_options = unique_campaigns_df[["campaign_id", "campaign_name"]].copy()

campaign_options['display_name'] = (
        campaign_options['campaign_id'].astype(str)
        + ' - '
        + campaign_options['campaign_name'].astype(str)
)

selected_display_name = st.selectbox(
    'Select a campaign', campaign_options['display_name'].tolist()
)

# Retrieve the campaign ID associated with the selected display label.
selected_row = campaign_options.loc[
    campaign_options['display_name'] == selected_display_name
].iloc[0]

selected_campaign_id = selected_row['campaign_id'].strip()


# Initialize the campaign-change tracker on the first app run.
if "last_campaign" not in st.session_state:
    st.session_state.last_campaign = selected_campaign_id

# Clear outputs that belong to the previous campaign when the user
# manually selects a different campaign from the dropdown.
if selected_campaign_id != st.session_state.last_campaign:
    st.session_state.executive_summary = None
    st.session_state.messages = []
    st.session_state.last_campaign = selected_campaign_id

# Synchronize the Streamlit selector with the application's existing
# analytics session object.
analytics_session.active_campaign_id = selected_campaign_id

st.write(f"Active campaign: {selected_campaign_id}")


# -------------------------------------------------------------------
# EXECUTIVE SUMMARY
# -------------------------------------------------------------------
if st.button("Generate Executive Summary"):
    with st.spinner("Generating Executive Summary..."):
        try:
            context = build_campaign_context(
                summary_df,
                campaign_goals_df,
                selected_campaign_id
            )

            # Load the dedicated executive-summary prompt.
            template = load_prompt("executive_summary")

            # Insert the campaign metrics into the prompt template
            final_prompt = build_prompt(template=template, variables={"campaign_metrics": context})

            # Send the completed prompt to the configured LLM.
            analysis = generate_analysis(final_prompt)

            # Save the result so it remains visible after Streamlit reruns.
            st.session_state.executive_summary = analysis

        except ValueError as e:
            # Display expected business/data errors without crashing the app.
            st.error(f"Analyst:{e}")

# Display the saved summary, or instructions when no summary exists.
if st.session_state.executive_summary:
    st.markdown(st.session_state.executive_summary)
else:
    st.info(
        "Click **Generate Executive Summary** "
        "to analyze the selected campaign."
    )


# -------------------------------------------------------------------
# ASK ANALYST — CHAT SHELL
#
# This currently proves that chat messages can be entered, displayed,
# and retained. The real router and analyst workflow will be connected
# in the next phase.
# -------------------------------------------------------------------

st.divider()
st.subheader("Ask Analyst")

# Rebuild the visible conversation from saved session-state messages.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input(
    "Ask a business question about campaign performance..."
)

if question:
    # Save and immediately display the user's submitted question.
    user_message = {
        "role": "user",
        "content": question,
    }

    st.session_state.messages.append(user_message)

    with st.chat_message("user"):
        st.markdown(question)

    # Temporary response used only to validate the chat interface.
    placeholder_answer = (
        "Ask Analyst integration is coming next."
    )

    assistant_message = {
        "role": "assistant",
        "content": placeholder_answer,
    }

    st.session_state.messages.append(assistant_message)

    with st.chat_message("assistant"):
        st.markdown(placeholder_answer)

