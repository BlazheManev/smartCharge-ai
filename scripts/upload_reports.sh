#!/bin/bash
set -e

# Upload Evidently Drift Reports
for file in reports/ev_drift/*.html; do
  station_id=$(basename "$file" .html)
  echo "📤 Uploading drift report for $station_id..."
  curl -X POST https://smartcharge-backend.onrender.comreports/upload \
       -F "type=drift" \
       -F "station_id=$station_id" \
       -F "file=@$file"
done

# Upload all GE Expectation reports (not just index)
echo "📤 Uploading GE Expectation HTML files..."
for file in gx/uncommitted/data_docs/local_site/expectations/*.html; do
  report_name=$(basename "$file" .html)
  echo "📤 Uploading GE report: $report_name"
  curl -X POST https://smartcharge-backend.onrender.comreports/upload \
       -F "type=expectation" \
       -F "station_id=global" \
       -F "file=@$file"
done
