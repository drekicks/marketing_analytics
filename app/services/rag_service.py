from openai import OpenAI
from app.config.settings import openai_api_key
from utils.knowledge_search import search_knowledge_base as search_knowledge

if not openai_api_key:
    raise RuntimeError("OPENAI_API_KEY is not set. Check your .env loading.")

client = OpenAI(api_key=openai_api_key)



def answer_with_rag(
    question: str,
    limit: int = 3,
    min_similarity: float = 0.35
) -> str:

    results = search_knowledge(question, limit=limit)

    if not results:
        return (
            "The available business documentation does not "
            "provide enough information to answer that question."
        )

    top_similarity = results[0]["similarity"]

    if top_similarity < min_similarity:
        return (
            "The available business documentation does not "
            "provide enough information to answer that question."
        )

    context = "\n\n".join(
        result["content"]
        for result in results
    )

    prompt = f"""
You are answering questions using governed business knowledge.

Use only the context provided below.
If the context does not contain enough information to answer the question,
say that the available business documentation does not provide enough information.

Formatting rules:
- Use Markdown formatting.
- Do not use LaTeX or mathematical notation such as \\[ \\], \\( \\), or \\text{{}}.
- Display formulas using plain text or inline code.
- Keep field names exactly as documented.

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

# if __name__ == "__main__":
#     question = "What does Pre-Lapsed mean?"
#
#     answer = answer_with_rag(question)
#
#     print(f"\nQuestion: {question}\n")
#     print(answer)