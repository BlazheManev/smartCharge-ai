import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class DatePreprocessor(BaseEstimator, TransformerMixin):
    def __init__(self, col):
        self.col = col

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()

        def robust_parse(val):
            try:
                ts = pd.to_datetime(val)
                if ts.tzinfo is None:
                    ts = ts.tz_localize("Europe/Ljubljana", ambiguous="NaT")
                else:
                    ts = ts.tz_convert("Europe/Ljubljana")
                return ts.tz_localize(None)
            except Exception:
                return pd.NaT

        X[self.col] = X[self.col].apply(robust_parse)
        invalid_rows = X[self.col].isna().sum()
        if invalid_rows > 0:
            print(f"⚠️ Dropped {invalid_rows} rows due to unparseable timestamps.")

        X = X.dropna(subset=[self.col])
        X = X.sort_values(by=self.col)

        print(f"🕒 Timestamp range: {X[self.col].min()} → {X[self.col].max()}")
        print(f"📈 Kept original rows: {len(X)}")

        return X


class SlidingWindowTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, window_size):
        self.window_size = window_size

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return self.create_sliding_windows(X, self.window_size)

    @staticmethod
    def create_sliding_windows(data, window_size):
        X, y = [], []
        for i in range(len(data) - window_size):
            X.append(data[i:i + window_size])
            y.append(data[i + window_size])
        return np.array(X), np.array(y)
