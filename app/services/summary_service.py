"""Executive summary for one campaign, shared by every UI and by typed requests."""

from app.ai.context_builder import build_campaign_context
from app.ai.llm_client_api import generate_analysis
from app.ai.prompt_builder import build_prompt
from app.ai.prompt_loader import load_prompt
from app.utils.data_loader import get_campaign_data


def generate_executive_summary(campaign_id: str) -> str:
    """Write the executive summary for a campaign with the dedicated summary prompt and model."""
    data = get_campaign_data()
    context = build_campaign_context(data.summary, data.goals, campaign_id)
    prompt = build_prompt(
        template=load_prompt("executive_summary"),
        variables={"campaign_metrics": context},
    )
    return generate_analysis(prompt, purpose="summary")
