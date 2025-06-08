import great_expectations as gx

context = gx.get_context()

datasource_name = "ev_charging"
data_asset_name = "ev_station_all"
expectation_suite_name = "ev_station_suite"

context.add_or_update_expectation_suite(expectation_suite_name=expectation_suite_name)

asset = context.get_datasource(datasource_name).get_asset(data_asset_name)
batch_request = asset.build_batch_request()

validator = context.get_validator(
    batch_request=batch_request,
    expectation_suite_name=expectation_suite_name
)

assistant_result = context.assistants.onboarding.run(
    validator=validator,
    exclude_column_names=[],
)

suite = assistant_result.get_expectation_suite()
context.save_expectation_suite(
    expectation_suite=suite,
    expectation_suite_name=expectation_suite_name
)

print("✅ Expectation suite for ALL stations created.")
