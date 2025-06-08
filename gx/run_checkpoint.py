import os
import sys
import great_expectations as gx

context = gx.get_context()
datasource_name = "ev_charging"
base_dir = "../data/preprocessed/ev"

valid_types = {
    "IEC62196Type2Outlet", "IEC62196Type2CableAttached", "IEC62196Type2CCS",
    "IEC62196Type1", "CHAdeMO", "TeslaSupercharger", "Other"
}

csv_files = [f for f in os.listdir(base_dir) if f.endswith(".csv")]
all_passed = True

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
        except (gx.exceptions.DataContextError, LookupError):
            print(f"➕ Registering new asset: {asset_name}")
            asset = datasource.add_csv_asset(
                name=asset_name,
                batching_regex=rf"{station_id}\.csv"
            )

        # Build batch request
        batch_request = asset.build_batch_request()

        # Check if expectation suite exists
        existing_suites = [s.expectation_suite_name for s in context.list_expectation_suites()]
        if suite_name not in existing_suites:
            print(f"🧠 Creating new expectation suite for: {station_id}")
            suite = context.add_expectation_suite(suite_name)

            # ⬅️ THIS is how you get the validator (NOT asset.get_validator())
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

            # Save suite
            validator.save_expectation_suite(discard_failed_expectations=False)

        # Create checkpoint if needed
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

        # Run the checkpoint
        result = checkpoint.run(run_id=f"{station_id}_run")
        if result["success"]:
            print(f"✅ PASSED: {station_id}")
        else:
            print(f"❌ FAILED: {station_id}")
            all_passed = False

    except Exception as e:
        print(f"❌ ERROR with {station_id}: {e}")
        all_passed = False

context.build_data_docs()

if all_passed:
    print("\n✅ All EV station validations passed!")
    sys.exit(0)
else:
    print("\n❌ One or more EV station validations failed.")
    sys.exit(1)
