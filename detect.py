"""Threat-detection logic: score traffic, classify attack type, assign severity, write alerts."""
import time
import joblib
import pandas as pd
from src import config
from src.features import add_features
from src.preprocess import split_xy


def severity(prob):
    if prob >= 0.95: return "CRITICAL"
    if prob >= 0.80: return "HIGH"
    if prob >= 0.50: return "MEDIUM"
    return "LOW"


def reason(row):
    """Human-readable evidence, like a SOC analyst would write in a ticket."""
    r = []
    if row["failed_logins"] >= 5: r.append(f"{int(row['failed_logins'])} failed logins")
    if row["request_rate"] > 100: r.append(f"request rate {row['request_rate']:.0f}/s")
    if row["unique_dst_ports"] > 20: r.append(f"{int(row['unique_dst_ports'])} ports probed")
    if row["syn_ratio"] > 0.7: r.append(f"SYN ratio {row['syn_ratio']:.2f}")
    return "; ".join(r) if r else "statistical deviation from normal profile"


def detect(df, threshold=0.5):
    """Return one alert row per suspicious flow."""
    X, _ = split_xy(df)
    rf = joblib.load(config.MODELS / "random_forest.joblib")
    clf = joblib.load(config.MODELS / "attack_type_classifier.joblib")
    iso = joblib.load(config.MODELS / "isolation_forest.joblib")

    out = df.copy()
    out["threat_score"] = rf.predict_proba(X)[:, 1]
    out["predicted_type"] = clf.predict(X)
    out["iso_anomaly"] = iso.predict(X) == -1

    known = out["threat_score"] >= threshold
    unknown = (~known) & out["iso_anomaly"]            # RF says fine, but behaviour is odd -> zero-day suspect
    alerts = out[known | unknown].copy()
    alerts["alert_type"] = alerts["predicted_type"].where(known[alerts.index], "Unknown Anomaly")
    alerts["alert_type"] = alerts["alert_type"].replace("Normal", "Unclassified Threat")
    alerts["severity"] = [severity(p) if k else "LOW" for p, k in zip(alerts["threat_score"], known[alerts.index])]
    alerts["evidence"] = alerts.apply(reason, axis=1)
    cols = ["timestamp", "src_ip", "dst_ip", "service", "alert_type", "severity",
            "threat_score", "evidence"]
    alerts = alerts[cols + (["attack_type"] if "attack_type" in alerts else [])]
    return alerts.sort_values("timestamp").reset_index(drop=True), out


def run(live=0):
    config.ensure_dirs()
    df = pd.read_csv(config.TEST_FILE, parse_dates=["timestamp"])
    df["timestamp"] = df["timestamp"].dt.floor("s")
    df_feat = df  # test file already contains engineered features
    alerts, scored = detect(df_feat)
    alerts.to_csv(config.OUTPUTS / "alerts.csv", index=False)
    scored.to_csv(config.OUTPUTS / "scored_traffic.csv", index=False)

    with open(config.OUTPUTS / "alerts.log", "w") as f:
        for _, a in alerts.iterrows():
            f.write(f"{a.timestamp} [{a.severity}] {a.alert_type} src={a.src_ip} dst={a.dst_ip} "
                    f"score={a.threat_score:.2f} | {a.evidence}\n")

    print(f"[detect] scanned {len(df):,} flows -> {len(alerts):,} alerts")
    print(alerts["severity"].value_counts().to_string())
    print(alerts["alert_type"].value_counts().to_string())

    n = live or 8     # --live N replays alerts like a real-time monitor; default shows a sample
    print("\n---------- LIVE ALERT FEED ----------")
    for _, a in alerts.head(n).iterrows():
        print(f"[{a.severity:8}] {a.timestamp} {a.alert_type:16} {a.src_ip:>15} -> {a.dst_ip:<10} "
              f"score={a.threat_score:.2f} | {a.evidence}")
        if live: time.sleep(0.2)
    return alerts, scored


if __name__ == "__main__":
    run()
