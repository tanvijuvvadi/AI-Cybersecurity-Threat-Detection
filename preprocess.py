"""Data cleaning + the scikit-learn preprocessing step (scaling + one-hot encoding)."""
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from src import config


def clean(df):
    """Remove duplicates, infinities and missing values (very common in CICIDS-style data)."""
    before = len(df)
    df = df.drop_duplicates().replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)
    print(f"[clean] {before:,} -> {len(df):,} rows (removed {before - len(df):,})")
    return df


def split_xy(df, target="label"):
    """Separate model inputs (X) from the answer (y); drop identifiers so the model can't memorise IPs."""
    drop = [c for c in config.ID_COLS + config.TARGET_COLS if c in df.columns]
    return df.drop(columns=drop), df[target]


def build_preprocessor(X):
    """Scale numeric columns, one-hot encode text columns. Lives inside a Pipeline -> fitted on TRAIN only."""
    cat = X.select_dtypes(include=["object", "category"]).columns.tolist()
    num = [c for c in X.columns if c not in cat]
    return ColumnTransformer([
        ("num", StandardScaler(), num),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
    ])
