# common/utils.py

from datetime import datetime
import numpy as np
import pandas as pd

def timestamp():
    return datetime.now().isoformat()

def normalize_series(series, min_val=0.0, max_val=1.0):
    norm = (series - np.min(series)) / (np.max(series) - np.min(series))
    return min_val + norm * (max_val - min_val)

def to_dataframe(records: list) -> pd.DataFrame:
    return pd.DataFrame(records)

def log(message):
    print(f"[{timestamp()}] {message}")
