import os
import sys
import great_expectations as gx
from great_expectations.exceptions import CheckpointNotFoundError, DataContextError

context = gx.get_context()
datasource_name = "ev_charging"
base_dir = "../data/preprocessed/ev"

valid_types = {
    "IEC62196Type2Outlet", "IEC62196Type2CableAttached", "IEC62196Type2CCS",
    "IEC62196Type1", "CHAdeMO", "TeslaSupercharger", "Other"
}

csv_files = [f for f in os.listdir(base_dir) if f.endswith(".csv")]
failed_stations = []

for csv_file in csv_files:
    station_id = csv_file.replace(".csv", "")
    asset_name = f"ev_station_{station_id}"
    checkpoint_name = f"checkpoint_ev_{station_id}"
    suite_name = f"ev_expectations_{station_id}"

    print(f"\n🚦 Running checkpoint for: {station_id}")

    try:
        datasource = context.get_datasource(datasource_name)

        try:
            asset = datasource.get_asset(asset_name)
        except (DataContextError, LookupError):
            print(f"➕ Registering new asset: {asset_name}")
            asset = datasource.add_csv_asset(
                name=asset_name,
                batching_regex=rf"{station_id}\.csv"
            )

        batch_request = asset.build_batch_request()

        # Delete suite if it exists (rebuild expectations)
        existing_suites = [s.expectation_suite_name for s in context.list_expectation_suites()]
        if suite_name in existing_suites:
            print(f"🧽 Deleting old expectation suite: {suite_name}")
            context.delete_expectation_suite(suite_name)

        # Create suite and validator
        context.add_expectation_suite(suite_name)
        validator = context.get_validator(
            batch_request=batch_request,
            expectation_suite_name=suite_name
        )

        # Add expectations
        validator.expect_column_to_exist("timestamp")
        validator.expect_column_values_to_not_be_null("timestamp")
        validator.expect_column_values_to_match_strftime_format("timestamp", "%Y-%m-%dT%H:%M:%S")

        validator.expect_column_values_to_not_be_null("lat")
        validator.expect_column_values_to_not_be_null("lon")
        validator.expect_column_values_to_be_between("lat", 45.3, 46.9)
        validator.expect_column_values_to_be_between("lon", 13.3, 16.6)

        validator.expect_column_values_to_be_in_set("type", list(valid_types))

        validator.expect_column_values_to_be_between("total", 0, 100)
        validator.expect_column_values_to_be_between("available", 0, 100)
        validator.expect_column_values_to_be_between("occupied", 0, 100)
        validator.expect_column_values_to_be_between("unknown", 0, 100)

        validator.save_expectation_suite(discard_failed_expectations=False)

        # Create checkpoint if not exists
        try:
            checkpoint = context.get_checkpoint(checkpoint_name)
        except CheckpointNotFoundError:
            print(f"🛠️ Creating checkpoint: {checkpoint_name}")
            checkpoint = context.add_checkpoint(
                name=checkpoint_name,
                validations=[{
                    "batch_request": batch_request,
                    "expectation_suite_name": suite_name
                }]
            )

        # Run checkpoint
        try:
            result = checkpoint.run(run_id=f"{station_id}_run")
            if result.get("success"):
                print(f"✅ PASSED: {station_id}")
            else:
                print(f"⚠️ Validation failed: {station_id} – but continuing")
                failed_stations.append(station_id)
        except Exception as e:
            print(f"❌ ERROR running checkpoint for {station_id}: {e}")
            failed_stations.append(station_id)

    except Exception as e:
        print(f"❌ ERROR processing {station_id}: {e}")
        failed_stations.append(station_id)

# Build Data Docs
context.build_data_docs()

# Final summary
if failed_stations:
    print("\n⚠️ Validation completed with failures in the following stations:")
    for sid in failed_stations:
        print(f" - {sid}")
else:
    print("\n✅ All EV station validations passed!")

# Always exit cleanly
print("\n🚀 Validation run complete. Results saved to Data Docs.")
sys.exit(0)
