import os
import json
import requests
from datetime import datetime
from time import sleep


API_KEY = "MGhthFNeQIv644euJYokp02evFVDrDM9"
if not API_KEY:
    raise ValueError("Missing TOMTOM_API_KEY environment variable")

OUTPUT_FILE = "data/raw/ev/ljubljana_ev_availability_combined.json"

CENTER_LAT = 46.04861
CENTER_LON = 14.50254
RADIUS_METERS = 26634
LIMIT = 100
CATEGORY = "7309"  # EV station

def fetch_ljubljana_ev_stations():
    print("📡 Fetching EV stations with availability in Ljubljana...")

    url = "https://api.tomtom.com/search/2/categorySearch/electric%20vehicle%20station.json"

    params = {
        "key": API_KEY,
        "lat": CENTER_LAT,
        "lon": CENTER_LON,
        "radius": RADIUS_METERS,
        "limit": LIMIT,
        "ofs": 0,
        "categorySet": CATEGORY,
        "openingHours": "nextSevenDays",
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        raw_results = response.json().get("results", [])
        print(f"🔍 Offset 0: {len(raw_results)} stations received")
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return

    # Filter unique stations by ID
    unique_stations = {}
    for station in raw_results:
        station_id = station.get("id")
        if station_id and station_id not in unique_stations:
            unique_stations[station_id] = station

    print(f"🧹 Deduplicated to {len(unique_stations)} unique stations")

    # Process each station
    processed = []
    count = 1
    for station in unique_stations.values():
        availability_id = station.get("dataSources", {}).get("chargingAvailability", {}).get("id")
        station_id = station.get("id")
        name = station.get("poi", {}).get("name", "Unnamed")
        address = station.get("address", {}).get("freeformAddress", "Unknown")

        if not availability_id or not station_id:
            continue

        # Fetch availability data
        availability_url = (
            f"https://api.tomtom.com/search/2/chargingAvailability.json"
            f"?key={API_KEY}&chargingAvailability={availability_id}"
        )
        try:
            r = requests.get(availability_url)
            r.raise_for_status()
            availability = r.json()
        except Exception as e:
            print(f"⚠️  Skipped {name} – failed to fetch availability: {e}")
            continue

        combined = {
            "id": station_id,
            "name": name,
            "address": address,
            "position": station.get("position"),
            "availability": availability.get("connectors", []),
            "fetched_at": datetime.now().isoformat()
        }

        processed.append(combined)
        print(f"✅ {count:03d}: {name} – {address}")
        count += 1

        sleep(0.25)

        if len(processed) >= 100:
            print("🛑 Reached 100 stations with availability.")
            break

    # Save to file
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({"results": processed}, f, indent=2)

    print(f"\n💾 Saved {len(processed)} stations to {OUTPUT_FILE}")

if __name__ == "__main__":
    fetch_ljubljana_ev_stations()
