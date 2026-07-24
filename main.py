import pandas as pd
from app.ai.prompt_builder import build_prompt
from app.ai.prompt_loader import load_prompt
from app.ai.context_builder import build_campaign_context
from app.config.paths import DATA_DIR
from app.ai.llm_client_api import generate_analysis
from app.ai.analyst_chat import ask_analyst


file_name="campaign_performance_summary.csv"
campaign_path = DATA_DIR / file_name
campaign_df = pd.read_csv(campaign_path,encoding='utf-8')

context = build_campaign_context(campaign_df,"CMP-2026-003")

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
]

for example in examples:
    print(f"• {example}")

print()
print ("Type 'exit' or 'quit' to close.")

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
    )
    print(f"\nAnalyst: {answer}")