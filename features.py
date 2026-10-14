"""Feature engineering: turn raw flow fields into signals that expose attacks."""
import numpy as np


def add_features(df):
    df = df.copy()
    df["bytes_per_packet"] = (df["src_bytes"] + df["dst_bytes"]) / df["packets"].clip(lower=1)
    df["byte_ratio"] = df["src_bytes"] / (df["dst_bytes"] + 1)               # upload- vs download-heavy
    df["packets_per_sec"] = df["packets"] / (df["duration"] + 0.01)          # burstiness
    df["login_fail_rate"] = df["failed_logins"] / (df["conn_count_60s"] + 1)
    df["port_spread"] = df["unique_dst_ports"] / (df["conn_count_60s"] + 1)  # scanning signal
    df["log_src_bytes"] = np.log1p(df["src_bytes"])
    df["log_dst_bytes"] = np.log1p(df["dst_bytes"])
    return df
