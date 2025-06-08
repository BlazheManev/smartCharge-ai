import os
import sys
import great_expectations as gx

# Always load context explicitly from the gx folder
context = gx.get_context(context_root_dir="gx")

# Set the base directory for preprocessed EV station files
base_dir = os.path.abspath(os.path.join("data", "preprocessed", "ev"))
datasource_name = "ev_charging"
asset_name = "all_ev_stations"

# Define valid EV plug types
valid_types = {
    "IEC62196Type2Outlet", "IEC62196Type2CableAttached", "IEC62196Type2CCS",
    "IEC62196Type1", "CHAdeMO", "TeslaSupercharger", "Other"
}

# Ensure directory exists
if not os.path.isdir(base_dir):
    print(f"❌ ERROR: Directory not found: {base_dir}")
    sys.exit(1)

# Get all CSV files
csv_files = [f for f in os.listdir(base_dir) if f.endswith(".csv")]
if not csv_files:
    print("❌ No CSV files found for validation.")
    sys.exit(1)

all_passed = True

for csv_file in csv_files:
    station_id = csv_file.replace(".csv", "")
    checkpoint_name = f"checkpoint_ev_{station_id}"
    suite_name = f"ev_expectations_{station_id}"
    csv_path = os.path.join(base_dir, csv_file)

    print(f"\n🚦 Validating station: {station_id}")

    try:
        datasource = context.get_datasource(datasource_name)
        asset = datasource.get_asset(asset_name)

        # Build batch request
        batch_request = asset.build_batch_request(
            {"path": csv_path}
        )

        # Create expectation suite if it doesn't exist
        existing_suites = [s.expectation_suite_name for s in context.list_expectation_suites()]
        if suite_name not in existing_suites:
            print(f"🧠 Creating expectation suite for: {station_id}")
            context.add_expectation_suite(suite_name)

            validator = context.get_validator(
                batch_request=batch_request,
                expectation_suite_name=suite_name
            )

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

        # Create or fetch checkpoint
        try:
            checkpoint = context.get_checkpoint(checkpoint_name)
        except gx.exceptions.CheckpointNotFoundError:
            print(f"🛠️ Creating checkpoint: {checkpoint_name}")
            checkpoint = context.add_checkpoint(
                name=checkpoint_name,
                validations=[{
                    "batch_request": batch_request,
                    "expectation_suite_name": suite_name
                }]
            )

        result = checkpoint.run(run_id=f"{station_id}_run")

        if result["success"]:
            print(f"✅ PASSED: {station_id}")
        else:
            print(f"❌ FAILED: {station_id}")
            all_passed = False

    except Exception as e:
        print(f"❌ ERROR validating {station_id}: {e}")
        all_passed = False

# Generate Data Docs
context.build_data_docs()

if all_passed:
    print("\n✅ All validations passed.")
    sys.exit(0)
else:
    print("\n❌ One or more validations failed.")
    sys.exit(1)
