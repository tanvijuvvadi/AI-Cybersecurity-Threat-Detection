"""
Virtual simulation of network traffic + cyber attacks.

Each row = one network flow (like a line in a firewall / Zeek / NetFlow log).
Attack signatures are modelled on real behaviour:
  DoS        -> huge request rate, many SYN packets, tiny duration, hundreds of connections
  BruteForce -> SSH/FTP target, many failed logins, repeated connections from few IPs
  PortScan   -> tiny flows touching MANY different destination ports
35% of attacks are "stealthy" (blended with normal behaviour) so detection is not trivial.
"""
import numpy as np
import pandas as pd
from src import config

NUMERIC = ["duration", "src_bytes", "dst_bytes", "packets", "failed_logins",
           "request_rate", "unique_dst_ports", "syn_ratio", "conn_count_60s"]


def _normal(n, rng):
    return pd.DataFrame({
        "duration": rng.gamma(2.0, 2.0, n),
        "protocol_type": rng.choice(["tcp", "udp", "icmp"], n, p=[.70, .25, .05]),
        "service": rng.choice(["http", "https", "dns", "smtp", "ssh", "ftp"], n,
                              p=[.30, .35, .20, .05, .07, .03]),
        "src_bytes": rng.lognormal(6.5, 1.0, n),
        "dst_bytes": rng.lognormal(7.5, 1.2, n),
        "packets": rng.poisson(20, n) + 1,
        "failed_logins": rng.choice([0, 1, 2], n, p=[.93, .05, .02]),
        "request_rate": rng.gamma(2, 3, n),
        "unique_dst_ports": rng.poisson(2, n) + 1,
        "syn_ratio": rng.beta(2, 8, n),
        "conn_count_60s": rng.poisson(8, n) + 1,
    })


def _dos(n, rng):
    return pd.DataFrame({
        "duration": rng.gamma(1.0, 0.2, n),
        "protocol_type": rng.choice(["tcp", "udp", "icmp"], n, p=[.6, .25, .15]),
        "service": rng.choice(["http", "https", "dns"], n, p=[.6, .3, .1]),
        "src_bytes": rng.lognormal(5.0, 0.8, n),
        "dst_bytes": rng.lognormal(3.0, 1.0, n),
        "packets": rng.poisson(400, n) + 50,
        "failed_logins": np.zeros(n),
        "request_rate": rng.gamma(20, 25, n),
        "unique_dst_ports": rng.poisson(1, n) + 1,
        "syn_ratio": rng.beta(9, 1.5, n),
        "conn_count_60s": rng.poisson(300, n) + 50,
    })


def _brute(n, rng):
    return pd.DataFrame({
        "duration": rng.gamma(3.0, 1.0, n),
        "protocol_type": ["tcp"] * n,
        "service": rng.choice(["ssh", "ftp", "smtp"], n, p=[.7, .2, .1]),
        "src_bytes": rng.lognormal(5.5, 0.5, n),
        "dst_bytes": rng.lognormal(5.0, 0.5, n),
        "packets": rng.poisson(40, n) + 5,
        "failed_logins": rng.poisson(10, n) + 3,
        "request_rate": rng.gamma(5, 4, n),
        "unique_dst_ports": np.ones(n),
        "syn_ratio": rng.beta(3, 5, n),
        "conn_count_60s": rng.poisson(40, n) + 10,
    })


def _scan(n, rng):
    return pd.DataFrame({
        "duration": rng.gamma(1.0, 0.1, n),
        "protocol_type": rng.choice(["tcp", "udp"], n, p=[.9, .1]),
        "service": rng.choice(["http", "https", "dns", "smtp", "ssh", "ftp"], n),
        "src_bytes": rng.lognormal(3.5, 0.5, n),
        "dst_bytes": rng.lognormal(2.5, 0.8, n),
        "packets": rng.poisson(2, n) + 1,
        "failed_logins": np.zeros(n),
        "request_rate": rng.gamma(6, 5, n),
        "unique_dst_ports": rng.poisson(60, n) + 20,
        "syn_ratio": rng.beta(8, 2, n),
        "conn_count_60s": rng.poisson(60, n) + 15,
    })


GENERATORS = {"Normal": _normal, "DoS": _dos, "BruteForce": _brute, "PortScan": _scan}
IP_POOLS = {"DoS": ("203.0.113.{}", 30), "BruteForce": ("198.51.100.{}", 5), "PortScan": ("192.0.2.{}", 3)}


def _make_ips(kind, n, rng):
    if kind == "Normal":
        return [f"192.168.1.{i}" for i in rng.integers(2, 60, n)]
    tpl, k = IP_POOLS[kind]
    return [tpl.format(i) for i in rng.integers(1, k + 1, n)]


def _make_times(kind, n, rng):
    day = 24 * 3600
    if kind == "Normal":
        secs = rng.uniform(0, day, n)
    else:   # attacks arrive in bursts (campaigns)
        centers = rng.uniform(3600, day - 3600, 2)
        secs = np.where(rng.random(n) < 0.8,
                        rng.choice(centers, n) + rng.normal(0, 600, n),
                        rng.uniform(0, day, n))
    secs = np.clip(secs, 0, day - 1)
    return pd.Timestamp("2026-01-01") + pd.to_timedelta(secs, unit="s")


def generate(n=config.N_FLOWS, seed=config.RANDOM_STATE, stealth_frac=0.35):
    rng = np.random.default_rng(seed)
    counts = {k: int(n * v) for k, v in config.ATTACK_MIX.items() if k != "Normal"}
    counts["Normal"] = n - sum(counts.values())
    frames = []
    for kind, cnt in counts.items():
        df = GENERATORS[kind](cnt, rng)
        df[NUMERIC] = df[NUMERIC].astype(float)
        if kind != "Normal":                      # stealthy attacks look closer to normal
            base = _normal(cnt, rng)
            mask = rng.random(cnt) < stealth_frac
            w = rng.uniform(0.3, 0.9, (mask.sum(), 1))      # how 'normal-looking' each stealth attack is
            df.loc[mask, NUMERIC] = (1 - w) * df.loc[mask, NUMERIC].values + w * base.loc[mask, NUMERIC].values
        df.insert(0, "dst_ip", [f"10.0.0.{i}" for i in rng.integers(1, 11, cnt)])
        df.insert(0, "src_ip", _make_ips(kind, cnt, rng))
        df.insert(0, "timestamp", _make_times(kind, cnt, rng))
        df["attack_type"] = kind
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    for c in ["src_bytes", "dst_bytes", "packets", "failed_logins", "unique_dst_ports", "conn_count_60s"]:
        out[c] = out[c].round().clip(lower=0).astype(int)
    out["duration"] = out["duration"].round(3)
    out["request_rate"] = out["request_rate"].round(2)
    out["syn_ratio"] = out["syn_ratio"].clip(0, 1).round(3)
    out["label"] = (out["attack_type"] != "Normal").astype(int)
    return out.sort_values("timestamp").reset_index(drop=True)


def run():
    config.ensure_dirs()
    df = generate()
    df.to_csv(config.RAW_FILE, index=False)
    print(f"[simulate] {len(df):,} flows saved -> {config.RAW_FILE}")
    print(df["attack_type"].value_counts().to_string())
    return df


if __name__ == "__main__":
    run()
