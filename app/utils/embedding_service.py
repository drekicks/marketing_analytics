from openai import OpenAI

from app.config.settings import openai_api_key

if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY is not set. Check your .env loading.")

client = OpenAI(api_key=openai_api_key)



def create_embedding(text: str) -> list[float]:
    response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
    return response.data[0].embedding

# from utils.knowledge_loader import load_knowledge_documents
# from utils.knowledge_chunker import chunk_document
#
#
# if __name__ == "__main__":
#     documents = load_knowledge_documents()
#
#     chunks = []
#
#     for document in documents:
#         chunks.extend(chunk_document(document))
#
#     first_chunk = chunks[0]
#
#     embedding = create_embedding(first_chunk["content"])
#
#     print(first_chunk["title"])
#     print(type(embedding))
#     print(len(embedding))
#     print(embedding[:10])