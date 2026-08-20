from app.utils.embedding_service import create_embedding
from app.utils.database import get_database_engine
from sqlalchemy import text

def cosine_similarity(vector_a, vector_b):
    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))

    magnitude_a = sum(a * a for a in vector_a) ** 0.5
    magnitude_b = sum(b * b for b in vector_b) ** 0.5

    return dot_product / (magnitude_a * magnitude_b)


def search_knowledge_base(question, limit=5):
    question_embedding = create_embedding(question)
    engine = get_database_engine()

    # 1. Check whether the question names a known category
    category_query = text("""
                          SELECT DISTINCT category
                          FROM ai.knowledge_chunks
                          WHERE category IS NOT NULL
                          """)

    with engine.connect() as conn:
        categories = conn.execute(category_query).scalars().all()

    question_lower = question.lower()

    matched_category = next(
        (
            category
            for category in categories
            if category.lower() in question_lower
        ),
        None
    )

    # 2. If a category is explicitly requested, retrieve that category
    if matched_category:
        query = text("""
                     SELECT id,
                            source,
                            category,
                            title,
                            content,
                            1.0 AS similarity
                     FROM ai.knowledge_chunks
                     WHERE category = :category
                     ORDER BY id
                     """)

        with engine.connect() as conn:
            return conn.execute(
                query,
                {"category": matched_category}
            ).mappings().all()

    # 3. Otherwise use semantic/vector retrieval
    question_embedding = create_embedding(question)

    query = text("""
        SELECT
            id,
            source,
            category,
            title,
            content,
            1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
        FROM ai.knowledge_chunks
        ORDER BY embedding <=> CAST(:embedding AS vector)
        LIMIT :limit
    """)

    with engine.connect() as conn:
        results = conn.execute(
            query,
            {
                "embedding": str(question_embedding),
                "limit": limit,
            }
        ).mappings().all()

    return results