from pymongo import MongoClient
from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import os
from dotenv import load_dotenv
import shutil

# Only load .env if running locally
if os.getenv("RAILWAY_ENVIRONMENT") is None:
    load_dotenv()

uri = os.getenv("MONGO_URI")
# Print debug
print("DEBUG: MONGO_URI =", os.getenv("MONGO_URI"))
if not uri:
    raise ValueError("MONGO_URI not found in environment variables")

def load_books_from_mongo():
    uri = os.getenv("MONGO_URI")
    client = MongoClient(uri)
    db = client["fantasy_books_db"]
    collection = db["books"]

    docs = []
    for book in collection.find():
        full_text = f"""
Title: {book.get('title', '')}
Author: {book.get('author', '')}
Description: {book.get('description', '') if book.get('description', '') else ', '.join(book.get('subjects', []))[:300]}
Publisher: {book.get('publisher', '')}
Publish Date: {book.get('publish_date', '')} 
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
            "rating_score": book.get("rating_score", 0),
            "publish_date": book.get("publish_date", ""),
            "language": book.get("language", ""),
            "publisher": book.get("publisher", ""),
            "pages": book.get("pages", 0),
            "subjects": book.get("subjects", []),
        }

        docs.append(Document(page_content=full_text, metadata=metadata))

    return docs

def create_and_save_faiss(docs, index_path="vectorstore"):
    if os.path.exists(index_path):
        shutil.rmtree(index_path)  
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(docs, embedding_model)
    vectorstore.save_local(index_path)

def load_faiss_index(index_path="vectorstore"):
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.load_local(index_path, embedding_model, allow_dangerous_deserialization=True)
    return vectorstore
