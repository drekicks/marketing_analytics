from app.utils.knowledge_loader import load_knowledge_documents
from app.utils.knowledge_chunker import chunk_document
from app.utils.embedding_service import create_embedding
from sqlalchemy import text
from app.utils.database import get_database_engine

def build_knowledge_chunks():
    documents = load_knowledge_documents()

    chunks = []

    for document in documents:
        chunks.extend(chunk_document(document))

    return chunks


def ingest_knowledge():
    chunks = build_knowledge_chunks()
    engine = get_database_engine()

    with engine.begin() as conn:
        print(f"Ingested {len(chunks)} knowledge chunks.")

        conn.execute(
            text("TRUNCATE TABLE ai.knowledge_chunks")
        )

        for chunk in chunks:
            embedding = create_embedding(chunk["content"])

            conn.execute(
                text("""
                    INSERT INTO ai.knowledge_chunks
                        (source, title, content, embedding, category)
                    VALUES
                        (:source, :title, :content, CAST(:embedding AS vector), :category)
                """),
                {
                    "source": chunk["source"],
                    "title": chunk["title"],
                    "content": chunk["content"],
                    "embedding": str(embedding),
                    "category": chunk["category"],
                }
            )

if __name__ == "__main__":
    ingest_knowledge()