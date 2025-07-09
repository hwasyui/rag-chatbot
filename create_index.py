# create_index.py
from chatbot import load_books_from_mongo, create_and_save_faiss
import os

if not os.path.exists("vectorstore/index.faiss"):
    docs = load_books_from_mongo()
    create_and_save_faiss(docs)
    print("Vector index created.")
else:
    print("Vector index already exists. Skipping creation.")
