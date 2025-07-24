import json
import os
import gridfs
from pymongo import MongoClient

# ✅ Config
MONGO_URI = "mongodb+srv://blazhe:Feri123feri@cluster0.j4co85k.mongodb.net/EV-AI?retryWrites=true&w=majority"
COLLECTION_NAME = "ml_models"
JSON_PATH = "public/ml_models.json"
MODELS_DIR = "models"

def upload_metadata(db):
    print("📦 Uploading ML model JSON to MongoDB...")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    collection = db[COLLECTION_NAME]
    deleted = collection.delete_many({})
    print(f"🗑️ Deleted {deleted.deleted_count} existing records from '{COLLECTION_NAME}'")
    result = collection.insert_many(data)
    print(f"✅ Inserted {len(result.inserted_ids)} model metadata records.")

def extract_station_id(filename):
    return filename.replace("pipeline_ev_", "").replace("model_ev_", "").replace(".pkl", "").replace(".onnx", "")

def upload_models_to_gridfs(db):
    print("📤 Uploading ONNX + Pipeline models to GridFS...")
    fs = gridfs.GridFS(db)
    for filename in os.listdir(MODELS_DIR):
        if not filename.endswith(".onnx") and not filename.endswith(".pkl"):
            continue
        filepath = os.path.join(MODELS_DIR, filename)
        existing = fs.find_one({"filename": filename})
        if existing:
            fs.delete(existing._id)
        station_id = extract_station_id(filename)
        with open(filepath, "rb") as f:
            fs.put(f, filename=filename, metadata={"station_id": station_id})
            print(f"✅ Uploaded: {filename} (station_id: {station_id})")

def main():
    client = MongoClient(MONGO_URI)
    db = client.get_default_database()
    upload_metadata(db)
    upload_models_to_gridfs(db)

if __name__ == "__main__":
    main()
