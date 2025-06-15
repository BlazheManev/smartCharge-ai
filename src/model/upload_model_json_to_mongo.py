import json
import os
from pymongo import MongoClient
import gridfs

# ✅ Config
MONGO_URI = "mongodb+srv://blazhe:Feri123feri@cluster0.j4co85k.mongodb.net/EV-AI?retryWrites=true&w=majority"
COLLECTION_NAME = "ml_models"
JSON_PATH = "public/ml_models.json"
MODELS_DIR = "models"

def upload_metadata(db):
    print("📦 Uploading ML model JSON to MongoDB...")

    # ✅ Load JSON data
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ✅ Collection
    collection = db[COLLECTION_NAME]

    # 🧹 Clear old metadata
    deleted = collection.delete_many({})
    print(f"🗑️ Deleted {deleted.deleted_count} existing records from '{COLLECTION_NAME}'")

    # ⬆️ Insert new metadata
    result = collection.insert_many(data)
    print(f"✅ Inserted {len(result.inserted_ids)} model metadata records.")

def upload_models_to_gridfs(db):
    print("📤 Uploading ONNX + Pipeline models to GridFS...")
    fs = gridfs.GridFS(db)

    for filename in os.listdir(MODELS_DIR):
        if not filename.endswith(".onnx") and not filename.endswith(".pkl"):
            continue

        filepath = os.path.join(MODELS_DIR, filename)

        # Remove existing file with same name
        existing = fs.find_one({"filename": filename})
        if existing:
            fs.delete(existing._id)

        # Upload file
        with open(filepath, "rb") as f:
            fs.put(f, filename=filename)
            print(f"✅ Uploaded: {filename}")

def main():
    client = MongoClient(MONGO_URI)
    db = client.get_default_database()

    upload_metadata(db)
    upload_models_to_gridfs(db)

if __name__ == "__main__":
    main()
