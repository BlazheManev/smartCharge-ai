#!/bin/bash
set -e

# Upload Evidently Drift Reports
for file in reports/ev_drift/*.html; do
  station_id=$(basename "$file" .html)

  echo "📤 Uploading drift report for $station_id..."
  curl -X POST https://ev-backend.vercel.app/reports/upload \
       -F "type=drift" \
       -F "station_id=$station_id" \
       -F "file=@$file"
done

# Upload Great Expectations Expectation Suite (index.html)
GE_FILE="gx/uncommitted/data_docs/local_site/expectations/index.html"

if [ -f "$GE_FILE" ]; then
  echo "📤 Uploading Great Expectations expectations report..."
  curl -X POST https://ev-backend.vercel.app//reports/upload \
       -F "type=expectations" \
       -F "station_id=global" \
       -F "file=@$GE_FILE"
fi
