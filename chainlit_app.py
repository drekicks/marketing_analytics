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
    from app.config.router import is_executive_summary_request, is_scope_request
    from app.config.settings import SessionState
    from app.services.analyst_service import process_analyst_question
    from app.ui.chainlit_support import (
        EXAMPLE_QUESTIONS,
        SQL_ELEMENT_NAME,
        SUMMARY_COMMAND,
        SUMMARY_QUESTION,
        added_campaigns,
        answer_label,
        campaign_label,
        campaign_options,
        campaign_profiles,
        campaign_switch_note,
        new_campaigns_note,
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


def _welcome_actions() -> list[cl.Action]:
    # The executive summary is a button in the message box (see _show_summary_button).
    actions = [
        cl.Action(name="refresh_data", payload={}, label="Refresh data", icon="refresh-cw"),
    ]
    actions += [
        cl.Action(name="example_question", payload={"question": question}, label=question)
        for question in EXAMPLE_QUESTIONS
    ]
    return actions


async def _show_summary_button() -> None:
    """Generate Executive Summary as a button that stays in the message box."""
    await cl.context.emitter.set_commands(
        [
            {"id": SUMMARY_COMMAND, "description": "Write the executive summary for the active campaign",
             "icon": "file-text", "button": True, "persistent": False},
        ]
    )


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


async def _sync_campaign_list() -> None:
    """Tell an open chat about campaigns added since it started (e.g. by the weekly job)."""
    try:
        data = await cl.make_async(get_campaign_data)()
    except Exception:  # noqa: BLE001 - the answer itself reports database problems
        return
    current = cl.user_session.get("campaign_options") or []
    latest = campaign_options(data.unique_campaigns)
    note = new_campaigns_note(added_campaigns(current, latest))
    cl.user_session.set("campaign_options", latest)
    if note:
        await cl.Message(content=note).send()


async def _answer(question: str) -> None:
    if cl.user_session.get("analytics_session") is None:
        await cl.Message(content="The app couldn't start. Please reload the page.").send()
        return

    await _sync_campaign_list()

    session = cl.user_session.get("analytics_session")
    options = cl.user_session.get("campaign_options")
    campaign_before = session.active_campaign_id
    is_summary = is_executive_summary_request(question)

    async with cl.Step(name="Writing executive summary" if is_summary else "Analysing", type="run") as step:
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

    if is_summary:
        content = f"## Executive summary: {campaign_label(options, result.campaign_id)}\n\n{parts.content}"
    else:
        # Which campaign the answer is about, then (only when it changed, e.g. after a
        # comparison) a highlighted note: the header menu keeps the chat's starting campaign.
        route = session.last_route
        if route is not None and route.analysis_type == "comparison":
            # "Compare CMP-A vs CMP-B" names both; "Compare to CMP-B" is relative to the active one.
            about = list(dict.fromkeys(route.campaign_ids if len(route.campaign_ids) > 1
                                       else [campaign_before, result.campaign_id]))
        else:
            about = [result.campaign_id]
        label = answer_label(
            [campaign_label(options, campaign_id) for campaign_id in about],
            all_campaigns=is_scope_request(question) and route is not None
            and route.context_type in ("insight", "customer_campaign"),
        )
        content = f"{label}\n\n{parts.content}"
        note = campaign_switch_note(options, campaign_before, session.active_campaign_id)
        if note:
            content = f"{content}\n\n{note}"

    await cl.Message(content=content, elements=elements).send()


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

    # The campaign menu in the header is Chainlit's chat profile selector; picking a
    # campaign starts a new chat, so each chat analyses one campaign.
    chosen = cl.user_session.get("chat_profile")
    valid_ids = {campaign_id for campaign_id, _ in options}
    active = chosen if chosen in valid_ids else options[0][0]

    cl.user_session.set("campaign_options", options)
    cl.user_session.set("analytics_session", SessionState(active_campaign_id=active))
    cl.user_session.set("analyst_history", [])

    await _show_summary_button()
    await _send_welcome()


@cl.set_chat_profiles
async def chat_profiles(current_user=None, language=None) -> list[cl.ChatProfile]:
    """One menu entry per campaign, read on each page load so new campaigns appear."""
    if startup_error is not None:
        return []
    try:
        data = await cl.make_async(get_campaign_data)()
    except Exception:  # noqa: BLE001 - on_chat_start shows the error
        logger.exception("Couldn't load campaigns for the campaign menu")
        return []

    return [
        cl.ChatProfile(
            name=profile.campaign_id,
            display_name=profile.label,
            markdown_description=profile.description,
            default=profile.default,
        )
        for profile in campaign_profiles(data.unique_campaigns)
    ]


@cl.on_message
async def on_message(message: cl.Message) -> None:
    if message.command == SUMMARY_COMMAND:
        # Same path as typing "Generate executive summary".
        await _answer(SUMMARY_QUESTION)
    if message.content.strip():
        await _answer(message.content)


# -------------------------------------------------------------------
# Buttons
# -------------------------------------------------------------------

@cl.action_callback("example_question")
async def on_example_question(action: cl.Action) -> None:
    question = action.payload.get("question", "")
    await cl.Message(content=question, type="user_message").send()
    await _answer(question)


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
    await cl.Message(
        content=(
            f"Data refreshed: {len(options)} campaigns available. "
            "Reload the page to see new campaigns in the campaign menu."
        )
    ).send()
