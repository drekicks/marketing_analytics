import re

def chunk_document(document):
    content = document["content"]
    source = document["source"]

    sections = re.split(r"(?=^## )", content, flags=re.MULTILINE)

    chunks = []

    for section in sections:
        section = section.strip()

        if not section.startswith("## "):
            continue

        lines = section.splitlines()

        title = lines[0].replace("## ", "").strip()

        chunks.append(
            {
            "source": source,
            "title": title,
            "content": section
            }
        )

    return chunks

# from app.utils.knowledge_loader import load_knowledge_documents
#
# if __name__ == "__main__":
#     documents = load_knowledge_documents()
#
#     for document in documents:
#         chunks = chunk_document(document)
#
#         for chunk in chunks:
#             print(chunk["source"])
#             print(chunk["title"])
#             print(len(chunk["content"]))
#             print("-" * 50)