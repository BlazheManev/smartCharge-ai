#!/bin/bash
set -e

# ✅ Your backend base URL
BACKEND_URL="https://smartcharge-backend.onrender.com"

# 🚀 Upload Evidently Drift Reports
echo "📤 Uploading Evidently drift reports..."
for file in reports/ev_drift/*.html; do
  [ -e "$file" ] || continue
  station_id=$(basename "$file" .html)

  echo "🔁 Uploading drift report: $station_id"
  curl -X POST "$BACKEND_URL/reports/upload" \
       -F "type=drift" \
       -F "station_id=$station_id" \
       -F "file=@$file"
done

# 🚀 Upload GE Expectation Reports
echo "📤 Uploading Great Expectations HTML files..."
for file in gx/uncommitted/data_docs/local_site/expectations/*.html; do
  [ -e "$file" ] || continue
  report_name=$(basename "$file" .html)

  echo "🔁 Uploading GE report: $report_name"
  curl -X POST "$BACKEND_URL/reports/upload" \
       -F "type=expectation" \
       -F "station_id=global" \
       -F "file=@$file"
done

echo "✅ All reports uploaded successfully."
