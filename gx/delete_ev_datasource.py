import great_expectations as gx

context = gx.get_context()

# Remove the old one if it exists
try:
    context.delete_datasource("ev_charging")
    print("✅ Deleted old 'ev_charging' datasource")
except Exception as e:
    print(f"⚠️ Could not delete: {e}")
