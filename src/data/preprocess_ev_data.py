import os
import json
import pandas as pd
from datetime import datetime
import pytz  # For timezone handling
from pymongo import MongoClient

# === Constants ===
INPUT_FILE = "data/raw/ev/ljubljana_ev_availability_combined.json"
OUTPUT_DIR = "data/preprocessed/ev"
MONGO_URI = "mongodb+srv://blazhe:Feri123feri@cluster0.j4co85k.mongodb.net/EV-AI?retryWrites=true&w=majority"

def preprocess_ev_data():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"{INPUT_FILE} not found")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    new_entries = 0
    slovenia_tz = pytz.timezone("Europe/Ljubljana")

    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    db = client["EV-AI"]
    collection = db["ev_station_availability"]

    for entry in data.get("results", []):
        station_id = entry.get("id")
        name = entry.get("name", "Unnamed")
        address = entry.get("address", "Unknown")
        connectors = entry.get("availability", [])
        position = entry.get("position", {})
        timestamp = entry.get("fetched_at")

        if not timestamp:
            timestamp = datetime.now(slovenia_tz).isoformat()
        else:
            try:
                timestamp = datetime.fromisoformat(timestamp)
                timestamp = timestamp.astimezone(slovenia_tz).isoformat()
            except Exception:
                timestamp = datetime.now(slovenia_tz).isoformat()

        if not station_id or not connectors:
            continue

        rows = []
        for conn in connectors:
            rows.append({
                "timestamp": timestamp,
                "name": name,
                "address": address,
                "lat": position.get("lat"),
                "lon": position.get("lon"),
                "type": conn.get("type"),
                "total": conn.get("total"),
                "available": conn.get("availability", {}).get("current", {}).get("available"),
                "occupied": conn.get("availability", {}).get("current", {}).get("occupied"),
                "unknown": conn.get("availability", {}).get("current", {}).get("unknown")
            })

        df_new = pd.DataFrame(rows)
        df_new = df_new.drop_duplicates(subset=["timestamp", "type"], keep="last")

        path = os.path.join(OUTPUT_DIR, f"{station_id}.csv")

        if os.path.exists(path):
            df_old = pd.read_csv(path)
            df_combined = pd.concat([df_old, df_new], ignore_index=True)
            df_combined.drop_duplicates(subset=["timestamp", "type"], keep="last", inplace=True)
        else:
            df_combined = df_new

        df_combined.sort_values("timestamp", inplace=True)
        df_combined.to_csv(path, index=False)
        print(f"✅ Updated: {path}")
        new_entries += 1

        # === Extract last 3 'occupied' values for prediction ===
        last_3_occupied = (
            df_combined["occupied"]
            .dropna()
            .astype(int)
            .tail(3)
            .tolist()
        )

        # === Save those last 3 to MongoDB ===
        collection.update_one(
            {"id": station_id},
            {"$set": {"last_occupied_values": last_3_occupied}},
            upsert=True
        )
        print(f"🧠 Saved last_occupied_values for {station_id}: {last_3_occupied}")

    print(f"\n📦 Done! {new_entries} stations processed.")

if __name__ == "__main__":
    preprocess_ev_data()
