from app.ai.prompt_builder import build_prompt
from app.ai.prompt_loader import load_prompt
from app.ai.context_builder import build_campaign_context,build_campaign_comparison_context,build_insight_context
from app.ai.llm_client_api import generate_analysis
from app.ai.analyst_chat import ask_analyst
from app.ai.session_state_manager import resolve_campaign_id,resolve_comparison_campaign_ids
from app.ui.campaign_selector import select_campaign
from datetime import datetime
from app.utils.data_loader import summary_df,campaign_goals_df,unique_campaigns_df,segment_df
from app.config.router import route_question
from app.config.settings import SessionState
# from app.config.settings import VisualizationRequest
from app.visualization.chart_builder import build_visualization_context
from app.visualization.chart_dispatcher import create_visualization
from app.config.paths import OUTPUT_DIR

session_state = SessionState()
# visualization_request = VisualizationRequest()
chart_dir = OUTPUT_DIR

campaign_id, campaign_name = select_campaign(
    unique_campaigns_df
)
valid_campaign_ids = {
    str(campaign).strip()
    for campaign in unique_campaigns_df["campaign_id"].dropna().tolist()
}
session_state.active_campaign_id = campaign_id
print(f"\nCampaign Selected: {campaign_name} ({campaign_id})")
print()
print("Generating Executive Summary...........")
print()

try:
    # route = route_question(question)

    context = build_campaign_context(
        summary_df,
        campaign_goals_df,
        campaign_id
    )

except ValueError as e:
    print(f"Analyst:{e}")
    raise SystemExit(1)


template = load_prompt("executive_summary")
question_template = load_prompt("analyst_guidelines")

final_prompt = build_prompt(template = template, variables={"campaign_metrics": context})

# print(f"Final prompt size: {len(final_prompt):,} characters")
# print(f"Approximate prompt tokens: {len(final_prompt) // 4:,}")

analysis = generate_analysis(final_prompt)

print(analysis)
print()
print("Executive Summary Complete")
print()
print("=" * 59)
print("Ask the Analyst is ready to answer questions.")
print("AI Marketing Analytics Assistant")
print("=" * 59)
print()
print("Ask a business question about the selected campaign.")
print()
print("Examples:")

examples = [
    "Which audience performed best?",
    "Should this campaign be scaled?",
    "What are the biggest business risks?",
    "Did the campaign achieve its objective?",
    "Across all campaigns, which audience performed best?",
]

for example in examples:
    print(f"• {example}")

print()
print ("Type 'exit' or 'quit' to close.")

conversation_history = []

scope_terms = (
    "overall",
    "across all",
    "across campaigns",
    "across segments",
    "portfolio-wide",
    "big picture",
    "holistically",
)

while True:
    question = input("\nYou: ").strip()

    if question.lower() in {"exit", "quit"}:
        print("Ask the Analyst closed.")
        break

    if not question:
        print("Please enter a question.")
        continue

    try:
        route = route_question(question)
        previous_active_campaign_id = session_state.active_campaign_id
        resolved_campaign_id = resolve_campaign_id(
            session_state=session_state,
            route=route,
            default_campaign_id=campaign_id,
            valid_campaign_ids=valid_campaign_ids,
        )
        normalized_question = question.lower()
        is_scope_request = any(term in normalized_question for term in scope_terms)

    # try:
        prebuilt_context = None
        # route = route_question(question)

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
                output_dir=chart_dir
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
            chart_name = f"{route.visualization_request.subject.title()} {route.visualization_request.metric.title()} - {resolved_campaign_id.upper()}.png"
            print(f"\nChart created: {chart_name}")
            print(f"Saved to: {chart_path.resolve()}\n")
            print(f"Campaign: {resolved_campaign_id}")
            print(f"Analyst: {answer}")
            continue

        comparison_campaign_ids = resolve_comparison_campaign_ids(
            explicit_campaign_ids=route.campaign_ids,
            previous_active_campaign_id=previous_active_campaign_id,
            fallback_campaign_id=campaign_id,
        )

        if route.context_type == "campaign" and route.analysis_type == "comparison" and len(comparison_campaign_ids) >= 2:
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
                None if is_scope_request and not route.campaign_ids else resolved_campaign_id,
            )

        answer = ask_analyst(
            campaign_id=resolved_campaign_id,
            question=question,
            prompt_template=question_template,
            conversation_history=conversation_history,
            context=prebuilt_context,
        )

    except ValueError as e:
        # print(f"Campaign: {resolved_campaign_id}")
        print(f"Analyst: {e}")
        continue

    conversation_history.append({
        "question": question,
        "answer": answer,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    )

    if not (route.context_type == "insight" and is_scope_request and not route.campaign_ids):
        print(f"\nCampaign: {resolved_campaign_id}")
    print(f"Analyst: {answer}")