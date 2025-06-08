import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class DatePreprocessor(BaseEstimator, TransformerMixin):
    def __init__(self, col, freq="5min"):
        self.col = col
        self.freq = freq

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()

        # Parse datetime robustly with UTC awareness
        X[self.col] = pd.to_datetime(X[self.col], utc=True, errors="coerce")

        # Drop rows where timestamp failed to parse
        X = X.dropna(subset=[self.col])

        # Convert to local timezone (Europe/Ljubljana) and remove tz info
        X[self.col] = X[self.col].dt.tz_convert("Europe/Ljubljana").dt.tz_localize(None)

        # Sort values by time
        X = X.sort_values(by=self.col)

        # Generate complete datetime range with 5-minute steps
        date_range = pd.date_range(start=X[self.col].min(), end=X[self.col].max(), freq=self.freq)
        date_df = pd.DataFrame({self.col: date_range})

        # Merge to ensure all time points exist
        X = pd.merge(date_df, X, on=self.col, how="left")

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
