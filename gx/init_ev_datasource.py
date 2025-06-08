import great_expectations as gx

context = gx.get_context()

# Register the datasource with a universal asset for all CSVs
datasource = context.sources.add_pandas_filesystem(
    name="ev_charging",
    base_directory="data/preprocessed/ev"
)

# One asset for all files — dynamic in run_checkpoint
datasource.add_csv_asset(
    name="ev_all_stations",
    batching_regex=r".*\.csv"
)

print("✅ ev_charging datasource with 'ev_all_stations' asset registered.")
