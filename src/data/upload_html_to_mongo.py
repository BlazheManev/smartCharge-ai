import os
import pymongo
from bs4 import BeautifulSoup


# Connect to MongoDB (will work with GH Actions secrets too)
client = pymongo.MongoClient("mongodb+srv://blazhe:Feri123feri@cluster0.j4co85k.mongodb.net/EV-AI?retryWrites=true&w=majority")
db = client.get_default_database()
collection = db.reports

# ❌ Drop old entries
collection.delete_many({})
print("🧹 Old reports deleted.")

# 📁 Report source folders
directories = {
    "drift": "reports/ev_drift",
    "expectation": "gx/uncommitted/data_docs/local_site/expectations",
}

# 📤 Parse & insert each HTML file
for report_type, folder in directories.items():
    if not os.path.exists(folder):
        print(f"⚠️ Folder does not exist: {folder}")
        continue

    for filename in os.listdir(folder):
        if not filename.endswith(".html"):
            continue

        filepath = os.path.join(folder, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")
        text_content = soup.get_text(separator="\n").strip()
        station_id = filename.split("_")[0]

        collection.insert_one({
            "station_id": station_id,
            "type": report_type,
            "filename": filename,
            "html": html_content,
            "text": text_content,
        })

        print(f"✅ Uploaded {filename} ({report_type})")

print("🚀 Done uploading all reports.")
