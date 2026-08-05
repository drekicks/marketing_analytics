from dataclasses import dataclass
from pathlib import Path
from app.config.router import route_question
from app.config.settings import SessionState
from app.ai.context_builder import build_campaign_context,build_campaign_comparison_context,build_insight_context
from app.utils.data_loader import summary_df,campaign_goals_df,unique_campaigns_df,segment_df
from app.ai.llm_client_api import generate_analysis
from app.ai.analyst_chat import ask_analyst
from app.ai.prompt_loader import load_prompt
from datetime import datetime
from app.ai.session_state_manager import resolve_campaign_id,resolve_comparison_campaign_ids
from app.visualization.chart_builder import build_visualization_context
from app.visualization.chart_dispatcher import create_visualization
from app.config.paths import OUTPUT_DIR

chart_dir = OUTPUT_DIR

@dataclass
class AnalystResult:
    answer: str
    campaign_id: str | None = None
    chart_path: Path | None = None
    chart_title: str | None = None


def process_analyst_question(
        question: str,
        session_state: SessionState,
        default_campaign_id: str,
        valid_campaign_ids: list[str],
        conversation_history: list[dict],
) -> AnalystResult:
    """
    Process one Ask Analyst question without depending on a specific UI.

    The CLI and Streamlit interfaces can both call this function and
    decide independently how to display the returned result.
    """

    # Determine the analytical route for the current question.
    route = route_question(question)

    # Load the instructions used for Ask Analyst responses.
    question_template = load_prompt("analyst_guidelines")

    # Maintain the previous active campaign ID.
    previous_active_campaign_id = session_state.active_campaign_id

    # For this first checkpoint, let ask_analyst build the
    # normal campaign or segment context internally.
    resolved_campaign_id = resolve_campaign_id(
        session_state=session_state,
        route=route,
        default_campaign_id=default_campaign_id,
        valid_campaign_ids=valid_campaign_ids,
    )

    # conversation_history=st.session_state.messages,

    scope_terms = (
        "overall",
        "across all",
        "across campaigns",
        "across segments",
        "portfolio-wide",
        "big picture",
        "holistically",
    )

    # previous_active_campaign_id = session_state.active_campaign_id

    normalized_question = question.lower()
    is_scope_request = any(term in normalized_question for term in scope_terms)

    prebuilt_context = None

    chart_path: Path | None = None

    if route.analysis_type == "visualization":
        if route.visualization_request is None:
            raise ValueError(
                "The visualization request could not be determined."
            )

        chart_path = create_visualization(
            request=route.visualization_request,
            campaign_id=resolved_campaign_id,
            campaign_ids=route.campaign_ids,
            segment_df=segment_df,
            summary_df=summary_df,
            output_dir=chart_dir,
        )

        visualization_context = build_visualization_context(
            request=route.visualization_request,
            campaign_id=resolved_campaign_id,
            campaign_ids=route.campaign_ids,
            segment_df=segment_df,
            summary_df=summary_df
        )

        analysis_instruction = f"""
                The application has already created the requested visualization.

                Original user request:
                {question}

                Interpret the supplied visualization data. Identify the clearest
                pattern, the highest and lowest values, and meaningful differences.

                Do not attempt to create the chart.
                Do not say that plotting or visualization is unavailable.
                Do not claim to have visually inspected the chart image.
                """.strip()

        answer = ask_analyst(
            campaign_id=resolved_campaign_id,
            question=analysis_instruction,
            prompt_template=question_template,
            conversation_history=conversation_history,
            context=visualization_context,
        )

    comparison_campaign_ids = resolve_comparison_campaign_ids(
        explicit_campaign_ids=route.campaign_ids,
        previous_active_campaign_id=previous_active_campaign_id,
        fallback_campaign_id=default_campaign_id,
    )

    if (route.context_type == "campaign" and
            route.analysis_type == "comparison"
            and len(comparison_campaign_ids) >= 2):
        prebuilt_context = build_campaign_comparison_context(
            summary_df,
            campaign_goals_df,
            comparison_campaign_ids,
        )

    elif route.context_type == "insight":
        prebuilt_context = build_insight_context(
            summary_df,
            segment_df,
            campaign_goals_df,
        (
            None
            if is_scope_request and not route.campaign_ids
            else resolved_campaign_id
        ),
    )

    answer = ask_analyst(
        campaign_id=resolved_campaign_id,
        question=question,
        prompt_template=question_template,
        conversation_history=conversation_history,
        context=prebuilt_context,
    )

    return AnalystResult(
        answer=answer,
        campaign_id=resolved_campaign_id,
        chart_path=chart_path,
    )

