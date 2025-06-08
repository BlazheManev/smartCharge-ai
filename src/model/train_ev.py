import os
import joblib
import random
import yaml
import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

from preprocess import DatePreprocessor, SlidingWindowTransformer

# Load global parameters
params = yaml.safe_load(open("params.yaml"))["train_ev"]
test_size = params["test_size"]
window_size = params["window_size"]
target_col = params["target_col"]
random_state = params["random_state"]

# Set reproducibility
os.environ["PYTHONHASHSEED"] = str(random_state)
random.seed(random_state)
np.random.seed(random_state)
tf.random.set_seed(random_state)

def build_model(input_shape):
    model = Sequential()
    model.add(LSTM(50, return_sequences=True, input_shape=input_shape))
    model.add(Dropout(0.2))
    model.add(LSTM(50, return_sequences=False))
    model.add(Dropout(0.2))
    model.add(Dense(1))
    model.compile(optimizer="adam", loss="mean_squared_error")
    return model

data_dir = "data/preprocessed/ev"
output_dir = "models"
os.makedirs(output_dir, exist_ok=True)

for filename in os.listdir(data_dir):
    if not filename.endswith(".csv"):
        continue

    station = filename.replace(".csv", "")
    print(f"\n🚀 Training model for station: {station}")

    df = pd.read_csv(os.path.join(data_dir, filename))

    if "timestamp" not in df.columns or target_col not in df.columns:
        print(f"⚠️ Skipping {station} due to missing 'timestamp' or '{target_col}' columns.")
        continue

    df = df[["timestamp", target_col]].copy()
    df.rename(columns={"timestamp": "date"}, inplace=True)

    date_preprocessor = DatePreprocessor("date")
    df = date_preprocessor.fit_transform(df)

    # 💡 Check available data after preprocessing
    non_null_count = df[target_col].notna().sum()
    print(f"ℹ️  {station}: {non_null_count} non-null '{target_col}' entries after preprocessing.")

    if non_null_count <= window_size + test_size:
        print(f"⚠️ Skipping {station}: not enough data after preprocessing.")
        continue

    df = df.drop(columns=["date"])

    df_test = df.iloc[-test_size:]
    df_train = df.iloc[:-test_size]

    numeric_transformer = Pipeline([
        ("fillna", SimpleImputer(strategy="mean")),
        ("normalize", MinMaxScaler())
    ])

    preprocess = ColumnTransformer([
        ("numeric_transformer", numeric_transformer, [target_col]),
    ])

    pipeline = Pipeline([
        ("preprocess", preprocess),
        ("sliding_window_transformer", SlidingWindowTransformer(window_size)),
    ])

    try:
        X_train, y_train = pipeline.fit_transform(df_train)
        X_test, y_test = pipeline.transform(df_test)
    except Exception as e:
        print(f"⚠️ Skipping {station} due to pipeline error: {e}")
        continue

    model = build_model((X_train.shape[1], X_train.shape[2]))
    early_stopping = EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True)
    model.fit(X_train, y_train, epochs=50, batch_size=32, validation_split=0.2, callbacks=[early_stopping])

    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    print(f"📊 {station} - MAE: {mae:.4f}, RMSE: {np.sqrt(mse):.4f}")

    # Retrain on full data
    X_full, y_full = pipeline.fit_transform(df)
    model = build_model((X_full.shape[1], X_full.shape[2]))
    model.fit(X_full, y_full, epochs=50, batch_size=32, validation_split=0.2, callbacks=[early_stopping])

    model.save(f"{output_dir}/model_{station}.keras")
    joblib.dump(pipeline, f"{output_dir}/pipeline_{station}.pkl")
    print(f"✅ Saved model and pipeline for {station}")
