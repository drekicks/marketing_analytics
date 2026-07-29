from app.ai.prompt_builder import build_prompt
from app.ai.prompt_loader import load_prompt
from app.ai.context_builder import (
    build_campaign_context,
    build_campaign_comparison_context,
)
from app.ai.llm_client_api import generate_analysis
from app.ai.analyst_chat import ask_analyst
from app.ui.campaign_selector import select_campaign
from datetime import datetime
from app.ai.context_loader import summary_df, campaign_goals_df, unique_campaigns_df
from app.config.router import route_question

campaign_id, campaign_name = select_campaign(
    unique_campaigns_df
)
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
    "Why did Win-Back underperform?",
    "What are the biggest business risks?",
    "Did the campaign achieve its objective?",
    "What were the goals of the campaign?",
]

for example in examples:
    print(f"• {example}")

print()
print ("Type 'exit' or 'quit' to close.")

conversation_history = []

while True:
    question = input("\nYou: ").strip()

    if question.lower() in {"exit", "quit"}:
        print("Ask the Analyst closed.")
        break

    if not question:
        print("Please enter a question.")
        continue

    route = route_question(question)

    if route.context_type == "campaign" and route.analysis_type == "comparison" and len(route.campaign_ids) >= 2:
        try:
            build_campaign_comparison_context(
                summary_df,
                campaign_goals_df,
                route.campaign_ids,
            )
        except ValueError as e:
            print(f"Analyst: {e}")
            continue


    try:
        answer = ask_analyst(
            campaign_id=campaign_id,
            question=question,
            prompt_template=question_template,
            conversation_history=conversation_history,
        )
    except ValueError as e:
        print(f"Analyst: {e}")
        continue

    conversation_history.append({
        "question": question,
        "answer": answer,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    )
    print(f"\nAnalyst: {answer}")