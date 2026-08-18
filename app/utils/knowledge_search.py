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

    query = text("""
        SELECT
            id,
            source,
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