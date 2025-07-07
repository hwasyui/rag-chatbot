import json
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings

def load_books(json_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        books = json.load(f)

    docs = []
    for book in books:
        full_text = f"""
Title: {book.get('title', '')}
Author: {book.get('author', '')}
Description: {book.get('description', '')}
Publisher: {book.get('publisher', '')}
Language: {book.get('language', '')}
Rating: {book.get('rating_score', '')} ({book.get('rating_count', '')} votes)
Pages: {book.get('pages', '')}
Subjects: {', '.join(book.get('subjects', [])) if isinstance(book.get('subjects'), list) else ''}
""".strip()

        metadata = {
            "title": book.get("title", ""),
            "image_url": book.get("image_url", ""),
            "rating_count": book.get("rating_count", 0),
            "author": book.get("author", ""),
            "description": book.get("description", ""),
            "rating_score": book.get("rating_score", 0)
        }

        docs.append(Document(page_content=full_text, metadata=metadata))

    return docs

def create_faiss_index(docs):
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(docs, embedding_model)
    return vectorstore
