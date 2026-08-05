from app.utils.data_loader import summary_df,campaign_goals_df,unique_campaigns_df,segment_df
from app.config.settings import SessionState
from app.services.analyst_service import process_analyst_question
from app.ai.context_builder import build_campaign_context
from app.ai.prompt_loader import load_prompt
from app.ai.prompt_builder import build_prompt
from app.ai.llm_client_api import generate_analysis


# Select the campaign and build the Executive Summary
def show_executive_summary(default_campaign_id: str,campaign_name) -> None:
    print(f"\nCampaign Selected: {campaign_name} ({default_campaign_id})")
    print()
    print("Generating Executive Summary...........")
    print()

    try:

        context = build_campaign_context(
            summary_df,
            campaign_goals_df,
            default_campaign_id
        )

    except ValueError as e:
        print(f"Analyst:{e}")
        raise SystemExit(1)

    template = load_prompt("executive_summary")

    final_prompt = build_prompt(template=template, variables={"campaign_metrics": context})

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
    print("Type 'exit' or 'quit' to close.")

# Ask the Analyst
# This calls process_analyst_question which is also used in the Streamlit app
def run_cli_chat(
        session_state: SessionState,
        default_campaign_id: str,
        valid_campaign_ids: set[str],
        conversation_history: list[str],
)-> None:

    while True:
        question = input("\nYou: ").strip()

        if question.lower() in {"exit", "quit"}:
            print("Ask the Analyst closed.")
            break

        if not question:
            print("Please enter a question.")
            continue

        try:
            result = process_analyst_question(
                question=question,
                session_state=session_state,
                default_campaign_id=default_campaign_id,
                valid_campaign_ids=valid_campaign_ids,
                conversation_history=conversation_history,
            )
        except ValueError as e:
            print(f"Error: {e}")
            continue

        print(f"\nCampaign: {result.campaign_id}")
        print(f"Analyst: {result.answer}")

        if result.chart_path:
            print(f"\nChart saved to: {result.chart_path}")