def chunk_document(document):
    content = document["content"]
    source = document["source"]

    lines = content.splitlines()

    chunks = []

    current_category = None
    current_title = None
    current_content = []

    for line in lines:
        stripped_line = line.strip()
        # print(repr(stripped_line))

        # Top-level category: # Customer Segments
        if stripped_line.startswith("# ") and not stripped_line.startswith("## "):

            # Save previous chunk before changing categories
            if current_title:
                chunks.append(
                    {
                        "source": source,
                        "category": current_category,
                        "title": current_title,
                        "content": "\n".join(current_content).strip(),
                    }
                )

                current_title = None
                current_content = []

            current_category = line.replace("# ", "", 1).strip()

            # print("CATEGORY FOUND:", current_category)

        # Chunk heading: ## Champion
        elif stripped_line.startswith("## "):

            # Save previous chunk
            if current_title:
                chunks.append(
                    {
                        "source": source,
                        "category": current_category,
                        "title": current_title,
                        "content": "\n".join(current_content).strip(),
                    }
                )

            current_title = stripped_line.replace("## ", "", 1).strip()

            current_content = [
                f"{current_category} > {current_title}",
                stripped_line,
            ]

        else:
            if current_title:
                current_content.append(line)

    # Save final chunk
    if current_title:
        chunks.append(
            {
                "source": source,
                "category": current_category,
                "title": current_title,
                "content": "\n".join(current_content).strip(),
            }
        )


    return chunks

# from app.utils.knowledge_loader import load_knowledge_documents
#
# if __name__ == "__main__":
#     documents = load_knowledge_documents()
#
#     for document in documents:
#         if document["source"] != "segments_v2.md":
#             continue
#
#         chunks = chunk_document(document)
#
#         for chunk in chunks:
#             print(chunk["source"])
#             print(chunk["category"])
#             print(chunk["title"])
#             print(len(chunk["content"]))
#             print("-" * 50)