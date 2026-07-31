# import anthropic
from openai import BadRequestError, OpenAI, OpenAIError

from app.config.settings import MODEL_NAME, openai_api_key


if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY is not set. Check your .env loading.")

client = OpenAI(api_key=openai_api_key)

# client = anthropic.Anthropic()

update_state_tool = {
    "name": "update_session_state",
    "description": (
        "Call this whenever the conversation establishes or changes the "
        "active campaign or segment. Only call it when the user has clearly "
        "specified or confirmed a value — not to guess."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "active_campaign_id": {
                "type": "string",
                "description": "The campaign the user wants to work with, if newly set."
            },
            "active_segment": {
                "type": "string",
                "description": "The audience segment the user wants to target, if newly set."
            },
        },
    },
}

def call_llm(state: SessionState, user_input: str) -> str:
    state.log_turn("user", user_input)

    system_prompt = f"""You are a marketing analytics assistant.

Current session context:
{state.to_prompt_context()}

Use the update_session_state tool whenever the user establishes or changes 
the active campaign or segment. After calling it, briefly confirm the 
change to the user."""

    messages = state.recent_turns() + [{"role": "user", "content": user_input}]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=system_prompt,
        tools=[update_state_tool],
        messages=messages,
    )

    # Loop while the model keeps calling tools
    while response.stop_reason == "tool_use":
        # Append the assistant's turn (text + tool_use blocks) as-is
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use" and block.name == "update_session_state":
                _apply_state_update(state, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": f"State updated: {state.to_prompt_context()}",
                })

        messages.append({"role": "user", "content": tool_results})

        # Refresh system prompt so the model sees the *new* state if it calls again
        system_prompt = f"""You are a marketing analytics assistant.

Current session context:
{state.to_prompt_context()}

Use the update_session_state tool whenever the user establishes or changes 
the active campaign or segment. After calling it, briefly confirm the 
change to the user."""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=system_prompt,
            tools=[update_state_tool],
            messages=messages,
        )

    # Final response is plain text
    reply_text = "".join(
        block.text for block in response.content if block.type == "text"
    )
    state.log_turn("assistant", reply_text)
    return reply_text


def _apply_state_update(state: SessionState, update: dict) -> None:
    if "active_campaign_id" in update:
        state.active_campaign_id = update["active_campaign_id"]
    if "active_segment" in update:
        state.active_segment = update["active_segment"]