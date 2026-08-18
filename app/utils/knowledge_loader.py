from app.config.paths import KNOWLEDGE_DIR

def load_knowledge_documents():
    documents = []

    for file_path in KNOWLEDGE_DIR.glob("*.md"):
        content = file_path.read_text(encoding="utf-8")

        documents.append(
            {
                "source": file_path.name,
                "content": content,
            }
        )
    return documents

# if __name__ == "__main__":
#     docs =load_knowledge_documents()
#
#     for doc in docs:
#         print(doc["source"])
#         print(len(doc["content"]))
#         print("-" * 50)