"""Central configuration: paths and constants used by every module."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
MODELS = ROOT / "models"
OUTPUTS = ROOT / "outputs"
IMAGES = ROOT / "images"

RAW_FILE = DATA_RAW / "simulated_traffic.csv"
TRAIN_FILE = DATA_PROCESSED / "train_traffic.csv"
TEST_FILE = DATA_PROCESSED / "test_traffic.csv"      # acts as "unseen live traffic"

RANDOM_STATE = 42
N_FLOWS = 20000
ATTACK_MIX = {"Normal": 0.80, "DoS": 0.08, "BruteForce": 0.06, "PortScan": 0.06}

# Identifier columns: kept for alerts, but NEVER given to the model (prevents memorising IPs)
ID_COLS = ["timestamp", "src_ip", "dst_ip"]
TARGET_COLS = ["attack_type", "label"]


def ensure_dirs():
    for d in (DATA_RAW, DATA_PROCESSED, MODELS, OUTPUTS, IMAGES):
        d.mkdir(parents=True, exist_ok=True)
