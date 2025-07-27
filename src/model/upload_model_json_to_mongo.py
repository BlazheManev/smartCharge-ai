import os
import json
import gridfs
from pymongo import MongoClient

# ✅ MongoDB Configuration
MONGO_URI = "mongodb+srv://blazhe:Feri123feri@cluster0.j4co85k.mongodb.net/EV-AI?retryWrites=true&w=majority"
DB_NAME = "EV-AI"
COLLECTION_NAME = "ml_models"
MODELS_DIR = "models"
JSON_PATH = "public/ml_models.json"  # Optional metadata file

def extract_station_id(filename):
    """
    Removes file prefixes and suffixes to isolate the station ID.
    """
    return filename.replace("pipeline_ev_", "").replace("model_ev_", "").replace(".pkl", "").replace(".onnx", "")

def upload_models_to_gridfs(db):
    """
    Uploads all .pkl and .onnx model files from the local models/ directory to MongoDB GridFS.
    """
    print("📤 Uploading ONNX + Pipeline models to GridFS...")
    fs = gridfs.GridFS(db)

    for filename in os.listdir(MODELS_DIR):
        if not filename.endswith(".onnx") and not filename.endswith(".pkl"):
            continue

        filepath = os.path.join(MODELS_DIR, filename)

        # Delete existing file if present
        existing = fs.find_one({"filename": filename})
        if existing:
            fs.delete(existing._id)
            print(f"🗑️ Deleted existing: {filename}")

        # Upload new file
        station_id = extract_station_id(filename)
        with open(filepath, "rb") as f:
            fs.put(f, filename=filename, metadata={"station_id": station_id})
            print(f"✅ Uploaded: {filename} (station_id: {station_id})")

def upload_metadata(db):
    """
    Optional: Uploads station metadata from JSON to a separate MongoDB collection.
    """
    if not os.path.exists(JSON_PATH):
        print("⚠️ Metadata JSON not found, skipping metadata upload.")
        return

    print("📦 Uploading ML model metadata to MongoDB...")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    collection = db[COLLECTION_NAME]
    deleted = collection.delete_many({})
    print(f"🗑️ Deleted {deleted.deleted_count} existing records from '{COLLECTION_NAME}'")

    result = collection.insert_many(data)
    print(f"✅ Inserted {len(result.inserted_ids)} metadata records.")

def main():
    print("🔌 Connecting to MongoDB...")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    # Upload models
    upload_models_to_gridfs(db)

    # Optional metadata
    upload_metadata(db)

if __name__ == "__main__":
    main()
