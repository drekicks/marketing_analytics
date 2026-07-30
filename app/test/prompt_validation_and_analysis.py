from openai import BadRequestError, OpenAI, OpenAIError

from app.config.settings import MODEL_NAME, openai_api_key


if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY is not set. Check your .env loading.")

client = OpenAI(api_key=openai_api_key)

# Conservative character-based guard.
# This is intentionally lower than many model limits because tokens are not
# equal to characters, and analytics prompts can contain dense tabular data.
MAX_PROMPT_CHARACTERS = 80_000


def _validate_prompt_size(prompt: str) -> None:
    """
    Validate prompt size before sending it to the LLM.

    This uses a conservative character limit because this project does not
    currently depend on a tokenizer package. The goal is to catch obviously
    oversized prompts locally and provide a useful error message before the
    API request fails with context_length_exceeded.
    """
    prompt_length = len(prompt)

    if prompt_length > MAX_PROMPT_CHARACTERS:
        raise ValueError(
            "Prompt is too large to send to the LLM. "
            f"Prompt length: {prompt_length:,} characters. "
            f"Configured limit: {MAX_PROMPT_CHARACTERS:,} characters. "
            "Reduce the amount of campaign context, customer-level detail, "
            "or conversation history before calling generate_analysis()."
        )


def generate_analysis(prompt: str) -> str:
    """
    Send an assembled analytics prompt to an LLM and return its text response.

    Args:
        prompt: Fully assembled prompt containing instructions and campaign data.

    Returns:
        Generated analysis as plain text.

    Raises:
        ValueError: If the prompt is empty or too large.
        RuntimeError: If the API request fails or returns no text.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    _validate_prompt_size(prompt)

    try:
        response = client.responses.create(
            model=MODEL_NAME,
            input=prompt,
        )

        analysis = response.output_text

        if not analysis or not analysis.strip():
            raise RuntimeError("LLM request returned no text.")

        return analysis.strip()

    except BadRequestError as e:
        error_message = str(e)

        if "context_length_exceeded" in error_message or "context window" in error_message:
            raise ValueError(
                "The assembled prompt exceeded the model context window. "
                "Reduce the prompt size by summarizing customer-level data, "
                "limiting conversation history, or using a smaller campaign context."
            ) from e

        raise RuntimeError(f"LLM request failed due to a bad request: {e}") from e

    except OpenAIError as e:
        raise RuntimeError(f"LLM request failed: {e}") from e
