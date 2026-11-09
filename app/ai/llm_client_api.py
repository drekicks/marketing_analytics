import json
import logging
import time
from dataclasses import dataclass, replace

from openai import BadRequestError, OpenAI, OpenAIError

from app.ai.markdown_cleanup import normalize_markdown
from app.config import settings
from app.config.settings import openai_api_key
from app.errors import ConfigurationError, LLMServiceError  # noqa: F401  (re-exported for callers)

logger = logging.getLogger(__name__)

client = OpenAI(api_key=openai_api_key)


@dataclass(frozen=True)
class ModelSettings:
    """Which model each kind of call uses, and the reasoning effort sent."""
    answer: str
    sql: str
    summary: str
    effort: str  # one of settings.REASONING_EFFORTS; "default" = don't send it


_DEFAULT_MODELS = ModelSettings(
    answer=settings.MODEL_NAME,
    sql=settings.SQL_MODEL_NAME,
    summary=settings.SUMMARY_MODEL_NAME,
    effort=settings.REASONING_EFFORT,
)
_models = _DEFAULT_MODELS

# Models that rejected the reasoning parameter; they're called without it.
_no_reasoning_models: set[str] = set()

# Optional list the model comparison script sets to collect per-call timings
# and token usage. None in the app.
usage_log: list[dict] | None = None


def current_models() -> ModelSettings:
    return _models


def configure_models(
        answer: str | None = None,
        sql: str | None = None,
        summary: str | None = None,
        effort: str | None = None,
) -> ModelSettings:
    """
    Override model settings at runtime (comparison script, tests).

    Pass no arguments to reset to the values from the environment. A changed
    answer model also becomes the SQL/summary model unless those are given.
    """
    global _models

    if answer is sql is summary is effort is None:
        _models = _DEFAULT_MODELS
        return _models

    if effort is not None:
        effort = effort.strip().lower()
        if effort not in settings.REASONING_EFFORTS:
            raise ConfigurationError(
                f"Reasoning effort must be one of {', '.join(settings.REASONING_EFFORTS)}; "
                f"got {effort!r}."
            )

    base = _models
    new_answer = answer or base.answer
    _models = replace(
        base,
        answer=new_answer,
        sql=sql or (new_answer if answer else base.sql),
        summary=summary or (new_answer if answer else base.summary),
        effort=effort or base.effort,
    )
    return _models


def _is_reasoning_rejection(error: BadRequestError) -> bool:
    message = str(error).lower()
    return "reasoning" in message or "effort" in message


def _create_response(model: str, purpose: str, **kwargs):
    """Call the Responses API with the configured reasoning effort.

    If the model rejects the reasoning parameter (a non-reasoning model, or an
    effort value it doesn't support), retry once without it and remember the
    model so later calls skip it.
    """
    effort = _models.effort
    send_reasoning = effort != "default" and model not in _no_reasoning_models
    if send_reasoning:
        kwargs["reasoning"] = {"effort": effort}

    started = time.perf_counter()
    try:
        response = client.responses.create(model=model, **kwargs)
    except BadRequestError as error:
        if not (send_reasoning and _is_reasoning_rejection(error)):
            raise
        logger.warning(
            "Model %s rejected reasoning effort %r; retrying without it.", model, effort
        )
        _no_reasoning_models.add(model)
        kwargs.pop("reasoning", None)
        response = client.responses.create(model=model, **kwargs)

    if usage_log is not None:
        usage = getattr(response, "usage", None)
        usage_log.append(
            {
                "purpose": purpose,
                "model": model,
                "effort": effort if "reasoning" in kwargs else "default",
                "seconds": round(time.perf_counter() - started, 3),
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
            }
        )

    return response


MAX_PROMPT_CHARACTERS = 400_000


def _get_prompt_size_message(prompt: str) -> str:
    prompt_characters = len(prompt)
    estimated_tokens = prompt_characters // 4

    return (
        f"Prompt size: {prompt_characters:,} characters "
        f"(approximately {estimated_tokens:,} tokens)"
    )


def _validate_prompt_size(prompt: str) -> None:
    prompt_length = len(prompt)

    # print(_get_prompt_size_message(prompt))

    if prompt_length > MAX_PROMPT_CHARACTERS:
        raise ValueError(
            "Prompt is too large to send to the LLM. "
            f"Prompt length: {prompt_length:,} characters. "
            f"Configured limit: {MAX_PROMPT_CHARACTERS:,} characters. "
            "Reduce the amount of campaign context, customer-level detail, "
            "or conversation history before calling generate_analysis()."
        )


def generate_analysis(prompt: str, purpose: str = "answer") -> str:
    """
    Send an assembled analytics prompt to an LLM and return its text response.

    Args:
        prompt: Fully assembled prompt containing instructions and campaign data.
        purpose: "answer" (chat, charts, definitions; OPENAI_MODEL) or
            "summary" (executive summary; OPENAI_SUMMARY_MODEL).

    Returns:
        Generated analysis as plain text.

    Raises:
        ValueError: If the prompt is empty or too large.
        LLMServiceError: If the API request fails or returns no text.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    _validate_prompt_size(prompt)

    try:
        model = _models.summary if purpose == "summary" else _models.answer
        response = _create_response(model, purpose, input=prompt)

        analysis = response.output_text

        if not analysis or not analysis.strip():
            raise LLMServiceError("LLM request returned no text.")

        return normalize_markdown(analysis.strip())

    except BadRequestError as e:
        error_message = str(e)

        if "context_length_exceeded" in error_message or "context window" in error_message:
            raise ValueError(
                "The assembled prompt exceeded the model context window. "
                "Reduce the prompt size by summarizing customer-level data, "
                "limiting conversation history, or using a smaller campaign context."
            ) from e

        raise LLMServiceError(f"LLM request failed due to a bad request: {e}") from e

    except OpenAIError as e:
        raise LLMServiceError(f"LLM request failed: {e}") from e


def generate_json(prompt: str, schema_name: str, schema: dict) -> dict:
    """
    Send a prompt and return the model's reply parsed as JSON.

    Uses Responses API structured output, so the reply must match `schema`
    (a strict JSON Schema object). Used where the application needs
    machine-readable output, such as model-written SQL. Uses
    OPENAI_SQL_MODEL (falls back to OPENAI_MODEL).

    Raises:
        ValueError: If the prompt is empty or too large.
        LLMServiceError: If the API request fails or the reply is not valid JSON.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    _validate_prompt_size(prompt)

    try:
        response = _create_response(
            _models.sql,
            "sql",
            input=prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                }
            },
        )

    except BadRequestError as e:
        raise LLMServiceError(f"LLM request failed due to a bad request: {e}") from e

    except OpenAIError as e:
        raise LLMServiceError(f"LLM request failed: {e}") from e

    try:
        return json.loads(response.output_text)
    except (TypeError, json.JSONDecodeError) as e:
        raise LLMServiceError("LLM returned a reply that is not valid JSON.") from e
