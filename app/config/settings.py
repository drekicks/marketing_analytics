import os
from dotenv import load_dotenv
from dataclasses import dataclass
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
    raise RuntimeError("OPENAI_API_KEY is not configured.")

if not MODEL_NAME:
    raise RuntimeError("OPENAI_MODEL is not configured.")

@dataclass
class SessionState:
    active_campaign_id: str | None = None
    active_segment: str | None = None
    last_route: "RouteResult | None" = None

