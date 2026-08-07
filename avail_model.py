import os
from openai import OpenAI

from dotenv import load_dotenv

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.config.router import RouteResult


load_dotenv()

MODEL_NAME = os.getenv("OPENAI_MODEL")
openai_api_key = os.getenv("OPENAI_API_KEY")


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Retrieve and print all available model IDs for this specific key
models = [m.id for m in client.models.list()]
models.sort()
print("Available Models:", models)
