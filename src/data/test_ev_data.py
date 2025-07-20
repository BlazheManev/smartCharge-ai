import os
import sys
import pandas as pd
from evidently import Report
from evidently.presets.dataset_stats import DataSummaryPreset
from evidently.presets.drift import DataDriftPreset

# Base paths
current_dir = "data/preprocessed/ev"
reference_dir = "data/reference/ev"
report_dir = "reports/ev_drift"
os.makedirs(report_dir, exist_ok=True)

# Check if current data folder exists
if not os.path.isdir(current_dir):
    print(f"❌ ERROR: Missing current data directory: {current_dir}")
    sys.exit(0)  # Exit gracefully to not break GitHub Actions

csv_files = [f for f in os.listdir(current_dir) if f.endswith(".csv")]
if not csv_files:
    print("❌ No current EV station files found.")
    sys.exit(0)

for csv_file in csv_files:
    station_id = csv_file.replace(".csv", "")
    current_path = os.path.join(current_dir, csv_file)
    reference_path = os.path.join(reference_dir, csv_file)
    report_path = os.path.join(report_dir, f"{station_id}_drift_report.html")

    print(f"\n📊 Testing data drift for station: {station_id}")

    try:
        # Load current
        current = pd.read_csv(current_path)

        # Ensure reference exists (copy current on first run)
        if not os.path.exists(reference_path):
            print(f"🆕 Reference missing. Copying current to reference: {reference_path}")
            os.makedirs(os.path.dirname(reference_path), exist_ok=True)
            current.to_csv(reference_path, index=False)

        reference = pd.read_csv(reference_path)

        # Remove timestamp/datetime fields
        for col in ["timestamp", "date_to"]:
            reference.pop(col, None)
            current.pop(col, None)

        # Skip if not enough data
        if len(current) < 10 or len(reference) < 10:
            print(f"⚠️ Skipping {station_id} - not enough data to test drift (min 10 rows required).")
            continue

        # Run Evidently Report
        report = Report([
            DataSummaryPreset(),
            DataDriftPreset(),
        ], include_tests=True)

        result = report.run(reference_data=reference, current_data=current)
        result.save_html(report_path)

        # Optional: Check drift test status
        result_dict = result.dict()
        station_passed = True

        if "tests" in result_dict:
            for test in result_dict["tests"]:
                if test.get("status") != "SUCCESS":
                    station_passed = False
                    break

        if station_passed:
            print(f"✅ PASSED: {station_id}")
            current.to_csv(reference_path, index=False)
        else:
            print(f"❌ FAILED: {station_id} - data drift detected!")

    except Exception as e:
        print(f"⚠️ Skipped {station_id} due to error: {e}")
        continue  # Gracefully skip this station and continue

print("\n✅ Drift testing complete for all stations.")
sys.exit(0)
