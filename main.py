from app.ai.prompt_builder import build_prompt
from app.ai.prompt_loader import load_prompt
from app.ai.context_builder import (
    build_campaign_context,
    build_campaign_comparison_context,
    build_insight_context
)
from app.ai.llm_client_api import generate_analysis
from app.ai.analyst_chat import ask_analyst
from app.ai.session_state_manager import (
    resolve_campaign_id,
    resolve_comparison_campaign_ids,
)
from app.ui.campaign_selector import select_campaign
from datetime import datetime
from app.ai.context_loader import summary_df, campaign_goals_df, unique_campaigns_df, segment_df
from app.config.router import route_question
from app.config.settings import SessionState

session_state = SessionState()

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

    try:
        prebuilt_context = None

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
        print(f"Campaign: {resolved_campaign_id}")
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