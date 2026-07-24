from app.ai.llm_client_api import generate_analysis
from app.ai.prompt_builder import build_prompt

def ask_analyst(campaign_context: str,
                question: str,
                prompt_template: str) ->str:

    # validate inputs

    variables = {"campaign_context": campaign_context, "user_question": question}

    prompt = build_prompt(prompt_template, variables)

    answer = generate_analysis(prompt)

    return answer