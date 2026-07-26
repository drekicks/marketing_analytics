import pandas as pd
from app.ai.prompt_builder import build_prompt
from app.ai.prompt_loader import load_prompt
from app.ai.context_builder import build_campaign_context
from app.config.paths import DATA_DIR
from app.ai.llm_client_api import generate_analysis
from app.ai.analyst_chat import ask_analyst
from app.utils.file_utils import load_sql_extracts
from app.ui.campaign_selector import select_campaign
from datetime import datetime

file_name="campaign_performance_summary.csv"
campaign_path = DATA_DIR / file_name
campaign_df = pd.read_csv(campaign_path,encoding='utf-8')

unique_campaigns_query = load_sql_extracts(["unique_campaigns_list"])
unique_campaigns_df = unique_campaigns_query["unique_campaigns_list"]

campaign_id, campaign_name = select_campaign(
    unique_campaigns_df
)
print(f"\nCampaign Selected: {campaign_name} ({campaign_id})")
print()
print("Generating Executive Summary...........")
print()

context = build_campaign_context(
    campaign_df,
    campaign_id
)

# context = build_campaign_context(campaign_df,"CMP-2026-003")

template = load_prompt("executive_summary")
question_template = load_prompt("analyst_question")

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

    answer = ask_analyst(
        campaign_context=context,
        question=question,
        prompt_template=question_template,
        conversation_history=conversation_history,
    )

    conversation_history.append({
        "question": question,
        "answer": answer,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    )
    print(f"\nAnalyst: {answer}")