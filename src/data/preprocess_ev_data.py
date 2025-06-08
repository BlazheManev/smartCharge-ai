import os
import json
import pandas as pd
from datetime import datetime

INPUT_FILE = "data/raw/ev/ljubljana_ev_availability_combined.json"
OUTPUT_DIR = "data/preprocessed/ev"

def preprocess_ev_data():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"{INPUT_FILE} not found")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0

    for entry in data.get("results", []):
        station_id = entry.get("id")
        name = entry.get("name", "Unnamed")
        address = entry.get("address", "Unknown")
        connectors = entry.get("availability", [])
        position = entry.get("position", {})
        timestamp = entry.get("fetched_at")

        if not station_id or not connectors or not timestamp:
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

        df_new = pd.DataFrame(rows).drop_duplicates(subset=["timestamp", "type"], keep="last")

        # Build per-station directory and filename
        station_dir = os.path.join(OUTPUT_DIR, station_id)
        os.makedirs(station_dir, exist_ok=True)

        timestamp_short = datetime.fromisoformat(timestamp).strftime("%Y%m%d%H%M%S")
        output_path = os.path.join(station_dir, f"{timestamp_short}.csv")
        df_new.to_csv(output_path, index=False)

        print(f"✅ Saved: {output_path}")
        count += 1

    print(f"\n📦 Finished preprocessing {count} stations.")

if __name__ == "__main__":
    preprocess_ev_data()
