import pandas as pd
from app.ai.prompt_builder import build_prompt
from app.ai.prompt_loader import load_prompt
from app.ai.context_builder import build_campaign_context
from app.config.paths import DATA_DIR
from app.ai.llm_client_api import generate_analysis

file_name="campaign_performance_summary.csv"
campaign_path = DATA_DIR / file_name
campaign_df = pd.read_csv(campaign_path,encoding='utf-8')

context = build_campaign_context(campaign_df,"CMP-2026-003")

template = load_prompt("executive_summary")

final_prompt = build_prompt(template = template, variables={"campaign_metrics": context})

analysis = generate_analysis(final_prompt)

print(analysis)
