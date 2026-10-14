"""Dashboard-style graphs for the README / screenshots."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from src import config

sns.set_theme(style="whitegrid")
COLORS = {"Normal": "#4c9f70", "DoS": "#d1495b", "BruteForce": "#edae49", "PortScan": "#00798c"}


def _save(name):
    plt.tight_layout(); plt.savefig(config.IMAGES / name, dpi=150); plt.close()


def run():
    raw = pd.read_csv(config.RAW_FILE, parse_dates=["timestamp"])
    scored = pd.read_csv(config.OUTPUTS / "scored_traffic.csv", parse_dates=["timestamp"])
    alerts = pd.read_csv(config.OUTPUTS / "alerts.csv", parse_dates=["timestamp"])

    # 1. class distribution
    plt.figure(figsize=(6, 4))
    ax = sns.countplot(data=raw, x="attack_type", hue="attack_type", palette=COLORS, legend=False,
                       order=["Normal", "DoS", "BruteForce", "PortScan"])
    ax.set_title("Traffic Class Distribution (imbalanced, like real life)"); ax.set_xlabel("")
    for c in ax.containers: ax.bar_label(c)
    _save("01_class_distribution.png")

    # 2. attack timeline (bursts = campaigns)
    tl = raw.groupby([raw["timestamp"].dt.floor("30min"), "attack_type"]).size().unstack(fill_value=0)
    tl.drop(columns="Normal").plot(figsize=(9, 4), color=[COLORS[c] for c in tl.columns if c != "Normal"])
    plt.title("Attack Activity Over 24 Hours"); plt.ylabel("Flows per 30 min"); plt.xlabel("")
    _save("02_attack_timeline.png")

    # 3. behaviour comparison
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, col in zip(axes, ["request_rate", "failed_logins", "unique_dst_ports"]):
        sns.boxplot(data=raw, x="attack_type", y=col, hue="attack_type", palette=COLORS, legend=False, ax=ax,
                    order=["Normal", "DoS", "BruteForce", "PortScan"], showfliers=False)
        ax.set_title(col); ax.set_xlabel(""); ax.tick_params(axis="x", rotation=20)
    _save("03_feature_behaviour.png")

    # 4. threat score distribution
    plt.figure(figsize=(7, 4))
    sns.histplot(data=scored, x="threat_score", hue="attack_type", palette=COLORS, bins=40, multiple="stack")
    plt.axvline(0.5, color="k", ls="--"); plt.title("Model Threat Score (dashed = alert threshold)")
    _save("04_threat_score_distribution.png")

    # 9. alerts by severity
    plt.figure(figsize=(6, 4))
    order = [s for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW"] if s in alerts["severity"].unique()]
    sns.countplot(data=alerts, x="severity", hue="severity", order=order, legend=False,
                  palette={"CRITICAL": "#8d0801", "HIGH": "#d1495b", "MEDIUM": "#edae49", "LOW": "#7aa6c2"})
    plt.title("Alerts by Severity"); plt.xlabel("")
    _save("09_alerts_by_severity.png")

    # 10. top attacker IPs
    top = alerts["src_ip"].value_counts().head(10).sort_values()
    plt.figure(figsize=(7, 4)); top.plot(kind="barh", color="#d1495b")
    plt.title("Top 10 Suspicious Source IPs"); plt.xlabel("Alerts")
    _save("10_top_attacker_ips.png")

    # 11. detected anomalies on timeline
    plt.figure(figsize=(10, 4))
    normal = scored[scored["threat_score"] < 0.5]
    flagged = scored[scored["threat_score"] >= 0.5]
    plt.scatter(normal["timestamp"], normal["request_rate"], s=4, c="#4c9f70", alpha=.3, label="Normal")
    plt.scatter(flagged["timestamp"], flagged["request_rate"], s=8, c="#d1495b", alpha=.7, label="Flagged threat")
    plt.yscale("log"); plt.legend(); plt.title("Detected Threats vs Normal Traffic (request rate)")
    _save("11_detected_anomalies.png")
    print("[visualize] graphs saved to images/")


if __name__ == "__main__":
    run()
