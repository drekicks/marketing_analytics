from openai import OpenAI, OpenAIError
# from dotenv import load_dotenv
from app.config.settings import MODEL_NAME, openai_api_key

# load_dotenv()  # make sure .env is loaded

if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY is not set. Check your .env loading.")

client = OpenAI(api_key=openai_api_key)


def generate_analysis(prompt: str) -> str:
    """
        Send an assembled analytics prompt to an LLM and return its text response.

        Args:
            prompt: Fully assembled prompt containing instructions and campaign data.
            model: OpenAI model identifier.

        Returns:
            Generated analysis as plain text.

        Raises:
            ValueError: If the prompt is empty.
            RuntimeError: If the API request fails or returns no text.
        """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    try:
        response = client.responses.create(
            model=MODEL_NAME,
            input=prompt,
        )

        analysis = response.output_text

        if not analysis or not analysis.strip():
            raise RuntimeError("LLM request returned no text.")

        return analysis.strip()
    except OpenAIError as e:
        raise RuntimeError(f"LLM request failed: {e}") from e

    # # analysis = response.output_text
    #
    # if not analysis or not analysis.strip():
    #     raise RuntimeError("LLM request returned no text.")
    #
    # return analysis.strip()
    #
    #