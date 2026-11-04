"""
Chainlit chat UI for the AI Marketing Analytics Assistant.

Run:  chainlit run chainlit_app.py
A thin UI over the same back end as streamlit_app.py and the CLI:
process_analyst_question() answers questions, get_campaign_data() supplies
the campaign list, and user_message() turns errors into readable text.
"""

import logging
import sys
from datetime import datetime

import chainlit as cl
from chainlit.input_widget import Select

from app.ui.errors import user_message

logger = logging.getLogger(__name__)

# Chainlit's CLI applies nest_asyncio, which breaks asyncio task detection on Python 3.14:
# static files (favicon, logo) then fail with anyio.NoEventLoopError. Render uses 3.12.
if sys.version_info >= (3, 14):
    logger.warning(
        "Chainlit doesn't run correctly on Python %d.%d (nest_asyncio). "
        "Use a Python 3.12 or 3.13 environment for the Chainlit app.",
        *sys.version_info[:2],
    )

# Importing the app validates settings (OpenAI key and model). Keep the
# error so every chat can show it instead of crashing the server.
startup_error: Exception | None = None

try:
    from app.ai.context_builder import build_campaign_context
    from app.ai.llm_client_api import generate_analysis
    from app.ai.prompt_builder import build_prompt
    from app.ai.prompt_loader import load_prompt
    from app.config.settings import SessionState
    from app.services.analyst_service import process_analyst_question
    from app.ui.chainlit_support import (
        EXAMPLE_QUESTIONS,
        SQL_ELEMENT_NAME,
        campaign_label,
        campaign_options,
        reply_parts,
        welcome_text,
    )
    from app.utils.data_loader import clear_campaign_data_cache, get_campaign_data
except Exception as error:  # noqa: BLE001 - shown to the user in the chat
    startup_error = error
    logger.exception("Start-up failed")
else:
    # Warm up at process start so the first visitor doesn't wait for the
    # database to wake and the campaign data to load.
    try:
        get_campaign_data()
    except Exception:  # noqa: BLE001 - retried on the first chat
        logger.exception("Initial campaign data load failed; will retry per chat")


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

async def _send_error(prefix: str, error: Exception) -> None:
    await cl.Message(content=f"{prefix}{user_message(error)}").send()


def _campaign_settings(options: list[tuple[str, str]], active: str) -> cl.ChatSettings:
    return cl.ChatSettings(
        [
            Select(
                id="campaign",
                label="Campaign",
                items={label: campaign_id for campaign_id, label in options},
                initial_value=active,
            )
        ]
    )


def _welcome_actions() -> list[cl.Action]:
    actions = [
        cl.Action(name="executive_summary", payload={}, label="Generate executive summary", icon="file-text"),
        cl.Action(name="refresh_data", payload={}, label="Refresh data", icon="refresh-cw"),
    ]
    actions += [
        cl.Action(name="example_question", payload={"question": question}, label=question)
        for question in EXAMPLE_QUESTIONS
    ]
    return actions


async def _send_welcome() -> None:
    options = cl.user_session.get("campaign_options")
    session = cl.user_session.get("analytics_session")
    label = campaign_label(options, session.active_campaign_id)
    await cl.Message(content=welcome_text(label), actions=_welcome_actions()).send()


def _answer_question(question: str):
    """Run one question through the shared back end (blocking; called off the event loop)."""
    session = cl.user_session.get("analytics_session")
    history = cl.user_session.get("analyst_history")
    data = get_campaign_data()
    valid_ids = {
        str(campaign_id).strip()
        for campaign_id in data.unique_campaigns["campaign_id"].dropna()
    }

    return process_analyst_question(
        question=question,
        session_state=session,
        default_campaign_id=session.active_campaign_id,
        valid_campaign_ids=valid_ids,
        conversation_history=history,
    )


def _executive_summary(campaign_id: str) -> str:
    data = get_campaign_data()
    context = build_campaign_context(data.summary, data.goals, campaign_id)
    prompt = build_prompt(
        template=load_prompt("executive_summary"),
        variables={"campaign_metrics": context},
    )
    return generate_analysis(prompt, purpose="summary")


async def _answer(question: str) -> None:
    if cl.user_session.get("analytics_session") is None:
        await cl.Message(content="The app couldn't start. Please reload the page.").send()
        return

    async with cl.Step(name="Analysing", type="run") as step:
        step.input = question
        try:
            result = await cl.make_async(_answer_question)(question)
        except Exception as error:  # noqa: BLE001 - shown to the user
            step.output = "Failed"
            await _send_error("Analyst: ", error)
            return
        step.output = "Done"

    cl.user_session.get("analyst_history").append(
        {
            "question": question,
            "answer": result.answer,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )

    parts = reply_parts(result)
    elements = []
    if parts.chart_path:
        elements.append(cl.Image(name="chart", path=parts.chart_path, display="inline", size="large"))
    if parts.sql:
        elements.append(
            cl.Text(name=SQL_ELEMENT_NAME, content=parts.sql, language="sql", display="side")
        )

    await cl.Message(content=parts.content, elements=elements).send()


# -------------------------------------------------------------------
# Chat lifecycle
# -------------------------------------------------------------------

@cl.on_chat_start
async def on_chat_start() -> None:
    if startup_error is not None:
        await _send_error("The app couldn't start. ", startup_error)
        return

    try:
        data = get_campaign_data()
    except Exception as error:  # noqa: BLE001 - shown to the user
        await _send_error("The app couldn't start. ", error)
        return

    options = campaign_options(data.unique_campaigns)
    if not options:
        await cl.Message(content="No campaigns were found in the data.").send()
        return

    active = options[0][0]
    cl.user_session.set("campaign_options", options)
    cl.user_session.set("analytics_session", SessionState(active_campaign_id=active))
    cl.user_session.set("analyst_history", [])

    await _campaign_settings(options, active).send()
    await _send_welcome()


@cl.on_settings_update
async def on_settings_update(settings: dict) -> None:
    session = cl.user_session.get("analytics_session")
    new_campaign = settings.get("campaign")
    if session is None or not new_campaign or new_campaign == session.active_campaign_id:
        return

    # A manual campaign change starts a new analysis, as in the Streamlit app.
    session.active_campaign_id = new_campaign
    cl.user_session.set("analyst_history", [])
    await _send_welcome()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    await _answer(message.content)


# -------------------------------------------------------------------
# Buttons
# -------------------------------------------------------------------

@cl.action_callback("example_question")
async def on_example_question(action: cl.Action) -> None:
    question = action.payload.get("question", "")
    await cl.Message(content=question, type="user_message").send()
    await _answer(question)


@cl.action_callback("executive_summary")
async def on_executive_summary(action: cl.Action) -> None:
    session = cl.user_session.get("analytics_session")
    if session is None:
        await cl.Message(content="The app couldn't start. Please reload the page.").send()
        return

    label = campaign_label(cl.user_session.get("campaign_options"), session.active_campaign_id)

    async with cl.Step(name="Writing executive summary", type="run"):
        try:
            summary = await cl.make_async(_executive_summary)(session.active_campaign_id)
        except Exception as error:  # noqa: BLE001 - shown to the user
            await _send_error("Analyst: ", error)
            return

    await cl.Message(content=f"## Executive summary: {label}\n\n{summary}").send()


@cl.action_callback("refresh_data")
async def on_refresh_data(action: cl.Action) -> None:
    session = cl.user_session.get("analytics_session")
    if session is None:
        await cl.Message(content="The app couldn't start. Please reload the page.").send()
        return

    clear_campaign_data_cache()
    try:
        data = await cl.make_async(get_campaign_data)()
    except Exception as error:  # noqa: BLE001 - shown to the user
        await _send_error("Analyst: ", error)
        return

    options = campaign_options(data.unique_campaigns)
    cl.user_session.set("campaign_options", options)
    await _campaign_settings(options, session.active_campaign_id).send()
    await cl.Message(content=f"Data refreshed: {len(options)} campaigns available.").send()
