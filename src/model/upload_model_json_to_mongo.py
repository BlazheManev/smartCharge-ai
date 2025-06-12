import json
import os
from pymongo import MongoClient

# Config
MONGO_URI = "mongodb+srv://blazhe:Feri123feri@cluster0.j4co85k.mongodb.net/EV-AI?retryWrites=true&w=majority"
DB_NAME = "ev_ai"
COLLECTION_NAME = "ml_models"
JSON_PATH = "public/ml_models.json"

def main():
    print("📦 Uploading ML model JSON to MongoDB...")

    # Read JSON file
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # Drop old and insert new
    collection.drop()
    result = collection.insert_many(data)

    print(f"✅ Inserted {len(result.inserted_ids)} model records into MongoDB.")

if __name__ == "__main__":
    main()
