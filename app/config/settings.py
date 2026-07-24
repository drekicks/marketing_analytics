import os
from dotenv import load_dotenv

load_dotenv()

# MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
MODEL_NAME = os.getenv("OPENAI_MODEL")
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY is not configured.")

if not MODEL_NAME:
    raise RuntimeError("OPENAI_MODEL is not configured.")