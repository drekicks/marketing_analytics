from app.ai.llm_client_api import generate_analysis
from app.ai.prompt_builder import build_prompt

def ask_analyst(campaign_context: str,
                question: str,
                prompt_template: str,
                conversation_history: list[dict[str,str]]
                ) ->str:

    # validate inputs

    # variables = {"campaign_context": campaign_context, "user_question": question}

    # prompt = build_prompt(prompt_template, variables)

    conversation_context = _format_conversation_history(conversation_history)

    final_prompt = build_prompt(
        template=prompt_template,
        variables={
            "campaign_context": campaign_context,
            # "campaign_metrics": campaign_context,
            "conversation_history": conversation_context,
            "question": question,
        },
    )

    return generate_analysis(final_prompt)


def _format_conversation_history(
    conversation_history: list[dict[str, str]],
    max_exchanges: int = 5,
) -> str:
    if not conversation_history:
        return ""

    recent_history = conversation_history[-max_exchanges:]

    formatted_exchanges = []

    for exchange in recent_history:
        formatted_exchanges.append(
            f"User: {exchange['question']}\n"
            f"Analyst: {exchange['answer']}"
        )

    return "\n\n".join(formatted_exchanges)