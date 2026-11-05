import re
from dataclasses import dataclass, replace
from pathlib import Path
from app.config.router import RouteResult, is_scope_request, route_question
from app.config.settings import SessionState
from app.ai.context_builder import build_campaign_comparison_context,build_insight_context
from app.utils.data_loader import DATA_SOURCE, get_campaign_data
from app.ai.analyst_chat import ask_analyst
from app.ai.prompt_loader import load_prompt
from app.ai.session_state_manager import resolve_campaign_id,resolve_comparison_campaign_ids
from app.visualization.chart_builder import build_visualization_context
from app.visualization.chart_dispatcher import create_visualization
from app.config.paths import OUTPUT_DIR
from app.ai.campaign_id_validation import validate_campaign_ids
from app.services.customer_sql_service import (
    build_customer_query_context,
    run_customer_query,
)

chart_dir = OUTPUT_DIR

# Short follow-ups such as "What about Canada?" carry no routing keywords.
FOLLOW_UP_PATTERN = re.compile(r"^\s*(what about|how about|and|same for|what if)\b", re.IGNORECASE)

@dataclass
class AnalystResult:
    answer: str
    campaign_id: str | None = None
    chart_path: Path | None = None
    chart_title: str | None = None
    sql: str | None = None


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

    data = get_campaign_data()
    summary_df, segment_df, campaign_goals_df = data.summary, data.segment, data.goals

    # Determine the analytical route for the current question.
    route = route_question(question)

    # Keep short follow-ups on the customer route ("What about Canada?"),
    # which the keyword router would otherwise send to a campaign summary.
    previous_route = session_state.last_route
    if (
        previous_route is not None
        and previous_route.context_type == "customer_campaign"
        and route.context_type == "campaign"
        and route.analysis_type == "summary"
        and FOLLOW_UP_PATTERN.match(question)
    ):
        route = replace(route, context_type="customer_campaign", analysis_type="detail")

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

    scope_request = is_scope_request(question)

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
            route=route,
        )

        # Return the chart interpretation directly. Falling through would
        # call ask_analyst() again without the chart context and overwrite
        # this answer with a generic campaign/segment response.
        return AnalystResult(
            answer=answer,
            campaign_id=resolved_campaign_id,
            chart_path=chart_path,
        )

    if route.context_type == "customer_campaign":
        return _answer_customer_question(
            question=question,
            route=route,
            route_campaign_ids=route.campaign_ids,
            resolved_campaign_id=resolved_campaign_id,
            question_template=question_template,
            conversation_history=conversation_history,
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
            if scope_request and not route.campaign_ids
            else resolved_campaign_id
        ),
    )

    answer = ask_analyst(
        campaign_id=resolved_campaign_id,
        question=question,
        prompt_template=question_template,
        conversation_history=conversation_history,
        context=prebuilt_context,
        route=route,
    )

    return AnalystResult(
        answer=answer,
        campaign_id=resolved_campaign_id,
        chart_path=chart_path,
    )


def _answer_customer_question(
        question: str,
        route: RouteResult,
        route_campaign_ids: list[str],
        resolved_campaign_id: str,
        question_template: str,
        conversation_history: list[dict],
) -> AnalystResult:
    """
    Answer a customer-level question with guarded text-to-SQL.

    The model writes SQL against customer_analytic_layer (scoped to the
    campaigns in the question, or the active campaign), the query runs as a
    read-only role, and the small result is interpreted with the standard
    analyst prompt.
    """
    if DATA_SOURCE != "postgres":
        raise ValueError(
            "Customer-level questions need the Neon database "
            "(DATA_SOURCE=postgres)."
        )

    campaign_ids = list(dict.fromkeys(route_campaign_ids)) or [resolved_campaign_id]

    summary_df = get_campaign_data().summary

    validate_campaign_ids(summary_df=summary_df, campaign_ids=campaign_ids)

    campaign_names = dict(
        zip(
            summary_df["campaign_id"].astype(str),
            summary_df["campaign_name"].astype(str),
        )
    )

    query_result = run_customer_query(
        question=question,
        campaign_ids=campaign_ids,
        campaign_names=campaign_names,
        conversation_history=conversation_history,
    )

    answer = ask_analyst(
        campaign_id=resolved_campaign_id,
        question=question,
        prompt_template=question_template,
        conversation_history=conversation_history,
        context=build_customer_query_context(query_result),
        route=route,
    )

    return AnalystResult(
        answer=answer,
        campaign_id=resolved_campaign_id,
        sql=query_result.display_sql or query_result.sql,
    )
