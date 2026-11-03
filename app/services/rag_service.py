from app.ai.llm_client_api import generate_analysis
from app.utils.knowledge_search import search_knowledge_base as search_knowledge

NOT_ENOUGH_INFORMATION = (
    "The available business documentation does not "
    "provide enough information to answer that question."
)


def answer_with_rag(
    question: str,
    limit: int = 3,
    min_similarity: float = 0.35
) -> str:

    results = search_knowledge(question, limit=limit)

    if not results:
        return NOT_ENOUGH_INFORMATION

    top_similarity = results[0]["similarity"]

    if top_similarity < min_similarity:
        return NOT_ENOUGH_INFORMATION

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
- Use standard Markdown only.
- Do not use HTML tags such as <br>.
- Use Markdown bullets or Markdown line breaks when displaying multiple items.
- Do not use LaTeX or mathematical notation such as \\[ \\], \\( \\), or \\text{{}}.
- Display formulas using plain text or inline code.
- Keep field names exactly as documented.
- When a business rule contains multiple AND/OR conditions, explain the conditions in plain language or numbered steps rather than repeating the raw expression alone.
- When multiple related categories or definitions are returned, use a Markdown table when it improves readability.
- Treat requests to "define" and "explain" business concepts similarly: provide the definition plus a clear explanation of the applicable business rule.
- Follow explicit formatting instructions in the user's question.

Context:
{context}

Question:
{question}
"""

    # Same model (OPENAI_MODEL), client, size check and error handling as
    # every other answer in the app.
    return generate_analysis(prompt)
