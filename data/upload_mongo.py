import json
from pymongo import MongoClient

# ---- Step 1: MongoDB Connection ----
uri = "mongodb+srv://saikikukusuo:saikisaiki@rag-fantasy-books.kmivnbs.mongodb.net/"
client = MongoClient(uri)

# Choose database and collection
db = client["fantasy_books_db"]        
collection = db["books"]               

# ---- Step 2: Load JSON ----mo
with open("./data/cleaned_fantasy_books.json", "r", encoding="utf-8") as f:
    books_data = json.load(f)

# ---- Step 3: Optional - Clear existing data ----
collection.delete_many({})  # Comment out if you don't want to remove existing records

# ---- Step 4: Insert data ----
if isinstance(books_data, list):
    result = collection.insert_many(books_data)
    print(f"Inserted {len(result.inserted_ids)} documents.")
else:
    result = collection.insert_one(books_data)
    print("Inserted 1 document.")

# ---- Step 5: Preview ----
print("One sample document:")
print(collection.find_one())
