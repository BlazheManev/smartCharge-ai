import os
import joblib
import random
import yaml
import numpy as np
import pandas as pd
import tensorflow as tf
import tf2onnx
import mlflow
import mlflow.tensorflow

from tensorflow.keras.models import Model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.base import TransformerMixin

from preprocess import DatePreprocessor, SlidingWindowTransformer

# Load config
params = yaml.safe_load(open("params.yaml"))["train_ev"]
test_size = params["test_size"]
window_size = params["window_size"]
target_col = params["target"]
random_state = params["random_state"]
model_dir = params.get("model_path", "models")
os.makedirs(model_dir, exist_ok=True)

# Reproducibility
os.environ["PYTHONHASHSEED"] = str(random_state)
random.seed(random_state)
np.random.seed(random_state)
tf.random.set_seed(random_state)

# MLflow init
if os.getenv("CI"):
    mlflow.set_tracking_uri("https://dagshub.com/BlazheManev/smartcharge-ai.mlflow")
    os.environ["MLFLOW_TRACKING_USERNAME"] = 'BlazheManev'
    os.environ["MLFLOW_TRACKING_PASSWORD"] = '11bfefc758786562b31a6197b270a83255ff8694'
else:
    import dagshub
    dagshub.init(repo_owner="BlazheManev", repo_name="smartcharge-ai", mlflow=True)

mlflow.set_experiment("iis_ev_training")

# Gather CSVs
data_dir = "data/preprocessed/ev"
csv_files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
total_files = len(csv_files)

# LSTM model builder
def build_model(shape):
    inputs = Input(shape=shape, name="input")
    x = LSTM(50, return_sequences=True)(inputs)
    x = Dropout(0.2)(x)
    x = LSTM(50)(x)
    x = Dropout(0.2)(x)
    outputs = Dense(1, name="output")(x)
    model = Model(inputs, outputs)
    model.compile(optimizer="adam", loss="mean_squared_error")
    return model

# 💡 Fix: Wrapper to convert numpy array → DataFrame
class ArrayToDataFrame(TransformerMixin):
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        return pd.DataFrame(X)

# Loop over stations
for i, filename in enumerate(csv_files, start=1):
    station = filename.replace(".csv", "")
    print(f"\n🚗 Training model for EV station: {station} ({i}/{total_files})")

    df = pd.read_csv(os.path.join(data_dir, filename))
    if "timestamp" not in df.columns or target_col not in df.columns:
        print(f"⚠️ Skipping {station}: missing columns.")
        continue

    df = df[["timestamp", target_col]]
    df.rename(columns={"timestamp": "date"}, inplace=True)
    df = DatePreprocessor("date").fit_transform(df).drop(columns=["date"])

    if len(df) <= test_size + window_size:
        print(f"⚠️ Skipping {station}: insufficient data.")
        continue

    df_train = df.iloc[:-test_size]
    df_test = df.iloc[-test_size:]

    numeric_transformer = Pipeline([
        ("impute", SimpleImputer(strategy="mean")),
        ("scale", MinMaxScaler())
    ])

    preprocess = ColumnTransformer([
        ("num", numeric_transformer, [target_col])
    ])

    pipeline = Pipeline([
        ("prep", preprocess),
        ("to_df", ArrayToDataFrame()),  # ✅ FIX: wrap numpy -> DataFrame
        ("window", SlidingWindowTransformer(window_size))
    ])

    try:
        pipeline.fit(df_train)
        X_train, y_train = pipeline.transform(df_train)
        X_test, y_test = pipeline.transform(df_test)
    except Exception as e:
        print(f"❌ Pipeline error for {station}: {e}")
        continue

    if len(X_test) == 0 or len(y_test) == 0:
        print(f"⚠️ Skipping {station}: empty test set.")
        continue

    input_shape = (X_train.shape[1], X_train.shape[2])

    with mlflow.start_run(run_name=f"train_ev_{station}"):
        mlflow.log_params({
            "station": station,
            "test_size": test_size,
            "window_size": window_size,
            "target_col": target_col,
            "random_state": random_state
        })

        mlflow.tensorflow.autolog()

        model = build_model(input_shape)
        early_stop = EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True)

        print(f"📦 Training EV model for {station}")
        model.fit(
            X_train, y_train,
            epochs=15,
            batch_size=64,
            validation_split=0.2,
            callbacks=[early_stop],
            verbose=0
        )

        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mse)

        mlflow.log_metrics({
            "mae": mae,
            "mse": mse,
            "rmse": rmse
        })

        print(f"📊 {station} - MAE: {mae:.4f}, RMSE: {rmse:.4f}")

        if not os.getenv("CI"):
            print(f"💾 Exporting ONNX for {station}")
            spec = (tf.TensorSpec([None, *input_shape], tf.float32, name="input"),)
            onnx_model, _ = tf2onnx.convert.from_keras(model, input_signature=spec, opset=13)
            onnx_path = f"{model_dir}/model_ev_{station}.onnx"
            with open(onnx_path, "wb") as f:
                f.write(onnx_model.SerializeToString())
            mlflow.log_artifact(onnx_path)

        pipe_path = f"{model_dir}/pipeline_ev_{station}.pkl"
        joblib.dump(pipeline, pipe_path)
        mlflow.log_artifact(pipe_path)

print("\n🏁 All EV stations processed and logged with MLflow.")
