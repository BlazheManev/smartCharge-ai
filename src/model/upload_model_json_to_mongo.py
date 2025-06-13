import json
from pymongo import MongoClient

# ✅ Config
MONGO_URI = "mongodb+srv://blazhe:Feri123feri@cluster0.j4co85k.mongodb.net/EV-AI?retryWrites=true&w=majority"
COLLECTION_NAME = "ml_models"
JSON_PATH = "public/ml_models.json"

def main():
    print("📦 Uploading ML model JSON to MongoDB...")

    # ✅ Load JSON data
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ✅ Connect using the URI default DB
    client = MongoClient(MONGO_URI)
    db = client.get_default_database()
    collection = db[COLLECTION_NAME]

    # 🧹 Clear old data
    deleted = collection.delete_many({})
    print(f"🗑️ Deleted {deleted.deleted_count} existing records.")

    # ⬆️ Insert new model metadata
    result = collection.insert_many(data)
    print(f"✅ Inserted {len(result.inserted_ids)} new model records.")

if __name__ == "__main__":
    main()
