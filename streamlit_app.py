import streamlit as st
from app.utils.data_loader import campaign_goals_df, summary_df,segment_df, unique_campaigns_df
from app.ai.context_builder import build_campaign_context,build_campaign_comparison_context,build_insight_context
from app.ai.prompt_builder import build_prompt
from app.ai.prompt_loader import load_prompt
from app.ai.llm_client_api import generate_analysis

st.set_page_config(page_title="AI Marketing Analytics Assistant",
                   page_icon="📊",
                   layout="wide")


st.title("AI Marketing Analytics Assistant")

st.write(
    "Explore campaign performance, compare audiences, "
    "and generate AI-assisted insights."
)

if "executive_summary" not in st.session_state:
    st.session_state.executive_summary = None

campaign_options = unique_campaigns_df[["campaign_id", "campaign_name"]].copy()

campaign_options['display_name'] = (
        campaign_options['campaign_id'].astype(str)
        + ' - '
        + campaign_options['campaign_name'].astype(str)
)

selected_display_name = st.selectbox(
    'Select a campaign', campaign_options['display_name'].tolist()
)

selected_row = campaign_options.loc[
    campaign_options['display_name'] == selected_display_name
].iloc[0]

selected_campaign_id = selected_row['campaign_id'].strip()

if "last_campaign" not in st.session_state:
    st.session_state.last_campaign = selected_campaign_id

if selected_campaign_id != st.session_state.last_campaign:
    st.session_state.executive_summary = None
    st.session_state.last_campaign = selected_campaign_id

st.write(f"Active campaign: {selected_campaign_id}")

if st.button("Generate Executive Summary"):
    with st.spinner("Generating Executive Summary..."):

        try:

            context = build_campaign_context(
                summary_df,
                campaign_goals_df,
                selected_campaign_id
            )

        except ValueError as e:
            st.error(f"Analyst:{e}")
            st.stop()

        template = load_prompt("executive_summary")

        final_prompt = build_prompt(template=template, variables={"campaign_metrics": context})

        analysis = generate_analysis(final_prompt)

        st.session_state.executive_summary = analysis

if st.session_state.executive_summary:
    st.markdown(st.session_state.executive_summary)
else:
    st.info(
        "Click **Generate Executive Summary** "
        "to analyze the selected campaign."
    )
