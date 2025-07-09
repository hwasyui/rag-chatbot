# create_index.py
from chatbot import load_books_from_mongo, create_and_save_faiss

docs = load_books_from_mongo()
create_and_save_faiss(docs)
