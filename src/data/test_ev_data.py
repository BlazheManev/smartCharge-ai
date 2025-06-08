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
    sys.exit(1)

csv_files = [f for f in os.listdir(current_dir) if f.endswith(".csv")]
if not csv_files:
    print("❌ No current EV station files found.")
    sys.exit(1)

all_passed = True

for csv_file in csv_files:
    station_id = csv_file.replace(".csv", "")
    current_path = os.path.join(current_dir, csv_file)
    reference_path = os.path.join(reference_dir, csv_file)
    report_path = os.path.join(report_dir, f"{station_id}_drift_report.html")

    print(f"\n📊 Testing data drift for station: {station_id}")

    # Load current
    current = pd.read_csv(current_path)

    # Ensure reference exists (copy current on first run)
    if not os.path.exists(reference_path):
        print(f"🆕 Reference missing. Copying current to reference: {reference_path}")
        os.makedirs(os.path.dirname(reference_path), exist_ok=True)
        current.to_csv(reference_path, index=False)

    reference = pd.read_csv(reference_path)

    # Remove timestamp/datetime fields (if any)
    for col in ["timestamp", "date_to"]:
        if col in reference.columns:
            del reference[col]
        if col in current.columns:
            del current[col]

    # Run Evidently
    report = Report([
        DataSummaryPreset(),
        DataDriftPreset(),
    ], include_tests=True)

    result = report.run(reference_data=reference, current_data=current)
    result.save_html(report_path)

    # Check result as dict
    result_dict = result.dict()
    station_passed = True

    if "tests" in result_dict:
        for test in result_dict["tests"]:
            if test.get("status") != "SUCCESS":
                station_passed = False
                break

    if station_passed:
        print(f"✅ PASSED: {station_id}")
        # Replace reference with current
        current.to_csv(reference_path, index=False)
    else:
        print(f"❌ FAILED: {station_id} - data drift detected!")
        all_passed = False

# Final result
if all_passed:
    print("\n✅ All EV stations passed drift tests.")
    sys.exit(0)
else:
    print("\n❌ Some stations failed drift tests.")
    sys.exit(1)
