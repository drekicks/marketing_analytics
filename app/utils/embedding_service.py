from openai import OpenAIError

from app.ai.llm_client_api import client
from app.errors import LLMServiceError

# Must match the 1536-dimension vectors stored in ai.knowledge_chunks.
EMBEDDING_MODEL = "text-embedding-3-small"


def create_embedding(text: str) -> list[float]:
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
    except OpenAIError as e:
        raise LLMServiceError(f"Embedding request failed: {e}") from e

    return response.data[0].embedding
