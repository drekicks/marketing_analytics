import os
from dotenv import load_dotenv
from dataclasses import dataclass

from app.errors import ConfigurationError
from typing import TYPE_CHECKING

# try:
#     import streamlit as st
# except ImportError:
#     st = None

if TYPE_CHECKING:
    from app.config.router import RouteResult

# Local development
load_dotenv()

MODEL_NAME = None
openai_api_key = None

# First try Streamlit Secrets
# if st is not None:
#     MODEL_NAME = st.secrets.get("OPENAI_MODEL")
#     openai_api_key = st.secrets.get("OPENAI_API_KEY")

# Fall back to .env / environment variables
MODEL_NAME = MODEL_NAME or os.getenv("OPENAI_MODEL")
openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ConfigurationError(
        "OPENAI_API_KEY is not configured. Add it to .env or the app secrets."
    )

if not MODEL_NAME:
    raise ConfigurationError(
        "OPENAI_MODEL is not configured. Add it to .env or the app secrets."
    )

# Optional per-purpose overrides; each falls back to OPENAI_MODEL.
# Use a fast model for routine answers (OPENAI_MODEL) and keep a stronger one
# where quality changes the numbers (customer SQL) or is most visible (summary).
SQL_MODEL_NAME = (os.getenv("OPENAI_SQL_MODEL") or "").strip() or MODEL_NAME
SUMMARY_MODEL_NAME = (os.getenv("OPENAI_SUMMARY_MODEL") or "").strip() or MODEL_NAME

# Reasoning effort sent with every request ("default" = don't send it and use
# the model's own default). Lower effort answers faster.
REASONING_EFFORTS = ("none", "minimal", "low", "medium", "high", "xhigh", "default")
REASONING_EFFORT = (os.getenv("OPENAI_REASONING_EFFORT") or "low").strip().lower()

if REASONING_EFFORT not in REASONING_EFFORTS:
    raise ConfigurationError(
        f"OPENAI_REASONING_EFFORT must be one of {', '.join(REASONING_EFFORTS)}; "
        f"got {REASONING_EFFORT!r}."
    )

@dataclass
class SessionState:
    active_campaign_id: str | None = None
    active_segment: str | None = None
    last_route: "RouteResult | None" = None

