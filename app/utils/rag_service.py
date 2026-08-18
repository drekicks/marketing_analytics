from openai import OpenAI
from app.config.settings import openai_api_key
from utils.knowledge_search import search_knowledge_base as search_knowledge

if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY is not set. Check your .env loading.")

client = OpenAI(api_key=openai_api_key)



def answer_with_rag(question: str, limit: int = 3) -> str:
    results = search_knowledge(question, limit=limit)

    context = "\n\n".join(
        result["content"]
        for result in results
    )

    prompt = f"""
You are answering questions using governed business knowledge.

Use only the context provided below.
If the context does not contain enough information to answer the question,
say that the available business documentation does not provide enough information.

Context:
{context}

Question:
{question}
"""

    response = client.responses.create(
        model="gpt-5.5",
        input=prompt,
    )

    return response.output_text

if __name__ == "__main__":
    question = "What is the average tenure of Churn Watchlist customers?"

    answer = answer_with_rag(question)

    print(f"\nQuestion: {question}\n")
    print(answer)