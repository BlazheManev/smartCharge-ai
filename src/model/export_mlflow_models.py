import mlflow
import pandas as pd
import os

# Nastavi MLflow tracking URI na DagsHub
mlflow.set_tracking_uri("https://dagshub.com/BlazheManev/smartcharge-ai.mlflow")

# Dodaš okoljske spremenljivke za auth (v terminalu ali .env)
os.environ['MLFLOW_TRACKING_USERNAME'] = "BlazheManev"
os.environ['MLFLOW_TRACKING_PASSWORD'] = "11bfefc758786562b31a6197b270a83255ff8694"

# Preberi vse rune iz eksperimenta z ID 0
runs_df = mlflow.search_runs(experiment_ids=["0"])

# Izberi zanimive stolpce
selected = runs_df[[
    'run_id',
    'params.station',
    'params.window_size',
    'metrics.rmse',
    'metrics.mae',
    'start_time'
]].sort_values('start_time', ascending=False)

# Shrani kot JSON
selected.to_json("public/ml_models.json", orient="records", lines=False)
print("✅ Model metadata exported.")
