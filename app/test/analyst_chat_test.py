def ask_analyst(
    question: str,
    context: str,
    analyst_guidelines: str,
) -> str:
    if not isinstance(question, str):
        raise TypeError(
            f"question must be a string, received "
            f"{type(question).__name__}"
        )

    if not isinstance(context, str):
        raise TypeError(
            f"context must be a string, received "
            f"{type(context).__name__}"
        )

    if not isinstance(analyst_guidelines, str):
        raise TypeError(
            f"analyst_guidelines must be a string, received "
            f"{type(analyst_guidelines).__name__}"
        )

    prompt = f"""
{analyst_guidelines}

DATA CONTEXT
------------
{context}

USER QUESTION
-------------
{question}
""".strip()

    ...