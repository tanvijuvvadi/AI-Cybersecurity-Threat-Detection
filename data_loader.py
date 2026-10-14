"""Load a traffic dataset: the simulated file OR a real one (NSL-KDD, CICIDS2017, UNSW-NB15)."""
import pandas as pd
from src import config


def load_simulated():
    df = pd.read_csv(config.RAW_FILE, parse_dates=["timestamp"])
    print(f"[load] {df.shape[0]:,} rows x {df.shape[1]} columns")
    return df


def load_real_dataset(path, label_col, benign_value="BENIGN"):
    """
    Plug in a real dataset, e.g. CICIDS2017:
        df = load_real_dataset("data/raw/Monday-WorkingHours.csv", "Label", "BENIGN")
    Adds `attack_type` and binary `label`. CICIDS headers often have leading spaces -> stripped here.
    NOTE: real datasets have different feature names, so edit src/features.py accordingly.
    """
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    label_col = label_col.strip()
    df["attack_type"] = df[label_col].astype(str).str.strip()
    df["label"] = (df["attack_type"] != benign_value).astype(int)
    return df.drop(columns=[label_col])
