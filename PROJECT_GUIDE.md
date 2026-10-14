# AI-Powered Cybersecurity Threat Detection: Complete Student Guide

Sections A–M follow the order you requested. Code is in `src/`; this guide explains it.

---
## A. Project Explanation

**Simple language:** Imagine a security guard watching thousands of people enter a building every second. A rule-based guard only stops people on a "banned list". An AI guard learns what normal visitors look like and notices anyone behaving strangely, even if never seen before.

**Technical language:** We model network flows as feature vectors (duration, bytes, packet counts, SYN ratio, failed logins, ports touched, …). Supervised classifiers (Random Forest, Logistic Regression) learn P(attack | flow). An unsupervised Isolation Forest, trained only on normal traffic, scores deviation from the baseline and can flag unseen (zero-day) behaviour. Outputs feed an alerting layer with severity and evidence.

**Problems solved:** unknown attacks that static rules miss · alert fatigue (ranking by score) · scale (millions of events/day) · slow manual log analysis.

**Why it matters:** attacks are automated and AI-assisted; defenders need automated detection that adapts.

**Industry uses**
| Use case | What is detected | Example signals |
|---|---|---|
| Intrusion detection | DoS, scans, brute force | SYN ratio, ports probed, failed logins |
| Fraud detection | stolen cards / account takeover | unusual amount, location, velocity |
| Anomaly detection | insider threat, data exfiltration | upload spike at 3 AM |
| Malware detection | infected hosts, C2 beaconing | periodic outbound connections, file features |
| Network monitoring | misconfig + attacks | traffic baselines per host |

**Banks:** transaction fraud scoring in milliseconds, account-takeover detection. **IT/service companies:** managed SOC (SIEM + ML alert triage). **Product companies:** UEBA for employees, cloud-log monitoring, abuse/bot detection.

**Workflow:** data collection → preprocessing → feature engineering → model training → prediction → alert generation → dashboard. (Implemented in `main.py`.)

---
## B. Tech Stack Options
| | Option A (Easy) | Option B (Intermediate) | Option C (Advanced) |
|---|---|---|---|
| Tools | Python, Pandas, Scikit-learn, Matplotlib | A + Seaborn, Isolation Forest, Flask, Pipelines | B + TensorFlow/PyTorch autoencoder, Kafka, Docker, Streamlit/ELK |
| Data | NSL-KDD / simulated CSV | Simulated + CICIDS2017/UNSW-NB15 | Streaming PCAP/NetFlow |
| Difficulty | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Output | accuracy + confusion matrix | alerts, severity, API, dashboards | real-time pipeline + monitoring |
| GPU | No | No | Optional (deep learning) |

## C. Selected Approach → **Option B**
Strong GitHub proof (alerts, API, multiple models, honest evaluation), runs on any laptop in under a minute, teaches concepts interviewers ask about. This repo implements it.

---
## D. Architecture
```
 [Traffic Source] simulate_data.py / CICIDS CSV
        │  raw flows (timestamp, IPs, features, label)
        ▼
 [Preprocess]  clean(): duplicates, inf, NaN      → preprocess.py
        ▼
 [Features]    bytes/packet, packets/sec, port_spread, login_fail_rate…  → features.py
        ▼
 [Pipeline]    StandardScaler + OneHotEncoder (fit on train only)
        ▼
 [Models]      RF binary │ RF attack-type │ Isolation Forest   → train.py
        ▼
 [Detection]   threshold + severity + evidence + zero-day rule → detect.py
        ▼
 [Outputs]     alerts.csv · alerts.log · live feed · Flask API · 11 graphs
```
**Data flow:** raw CSV → cleaned DataFrame → engineered DataFrame → train/test split (test saved as "unseen live traffic") → saved `.joblib` pipelines → detection reads the test file, scores it, writes alerts.

---
## E. Folder Structure
```
AI-Cybersecurity-Threat-Detection/
├── data/raw/           generated or downloaded datasets (git-ignored CSVs)
├── data/processed/     train/test splits
├── notebooks/          EDA notebook (screenshots for README)
├── src/                all modules (config, simulate_data, data_loader, preprocess, features, train, evaluate, detect, visualize)
├── models/             saved .joblib pipelines
├── outputs/            metrics.csv, alerts.csv, alerts.log, classification_report.txt
├── images/             graphs used in README
├── docs/               this guide, notes
├── app.py              Flask API
├── main.py             pipeline runner
├── requirements.txt  .gitignore  README.md
```

## F. Installation
Python **3.10+** (tested on 3.12).

**Windows (PowerShell/CMD)**
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
If PowerShell blocks activation: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

**Mac / Linux**
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Create requirements later with `pip freeze > requirements.txt` (the supplied file already lists the minimum).

## G. Code, file by file
| File | Purpose |
|---|---|
| `src/config.py` | Paths, seed, class mix; one place to change settings |
| `src/simulate_data.py` | Generates normal + DoS + BruteForce + PortScan flows with IP pools, bursts and stealth attacks |
| `src/data_loader.py` | Loads simulated data or a real dataset (strips CICIDS column spaces) |
| `src/preprocess.py` | Cleaning, X/y split (drops IPs/timestamps), scaler + encoder |
| `src/features.py` | Engineered features (packets_per_sec, port_spread, byte_ratio…) |
| `src/train.py` | Stratified split; trains LR, RF, attack-type RF, Isolation Forest (normal-only) |
| `src/evaluate.py` | Accuracy/precision/recall/F1/ROC-AUC, confusion matrices, ROC, feature importance |
| `src/detect.py` | Scores traffic, classifies type, severity, evidence, zero-day rule, writes alerts |
| `src/visualize.py` | 6 dashboard graphs |
| `main.py` / `app.py` | CLI runner / REST API |

**Design decisions to mention in interviews**
- **Pipeline objects**: scaling/encoding is fitted only on training data → no data leakage.
- **IPs and timestamps are excluded** from model inputs, so the model learns behaviour rather than memorising addresses.
- **`class_weight="balanced"`** handles the 80/20 imbalance.
- **Isolation Forest trains on normal only**, which mirrors real life where labelled attacks are rare.
- **Zero-day rule**: flow that RF calls normal but Isolation Forest flags → `Unknown Anomaly` (LOW).

**Note on the sample code you pasted:** it has issues worth fixing in your own version. The Flask API sends 3 fields but the model was trained on all columns (shape mismatch); `StandardScaler` is computed but never used; scaling before the split leaks information; `CICIDS2017.csv` label columns usually need `.str.strip()`; and Random Forest does not need scaling. This repo fixes all of those.

---
## H. Virtual Simulation of Cyber Threats
**How the data represents real traffic:** each row is a flow like a NetFlow/Zeek record. Normal traffic: moderate rates, 0–2 failed logins, few ports. Attack signatures:
- **DoS:** request_rate ~500/s, SYN ratio >0.8, 300+ connections/min, tiny duration, many packets.
- **Brute force:** ssh/ftp, 3+ failed logins, repeated connections from 5 attacker IPs.
- **Port scan:** many unique destination ports (20–100+), tiny flows, high SYN ratio.
- **Stealth attacks (35%)**: same signature diluted toward normal, so detection isn't trivial.
- Attackers use external IP pools (203.0.113.x, 198.51.100.x, 192.0.2.x, reserved documentation ranges), arrive in **bursts**, and target internal hosts 10.0.0.x.

**How detection works:** RF gives threat_score → above 0.5 raises an alert; severity from score (≥0.95 CRITICAL, ≥0.80 HIGH, ≥0.50 MEDIUM); the type classifier labels the attack; evidence rules print why; Isolation Forest catches unknown behaviour.

**Simulation workflow**
1. `python main.py --step simulate`: generate the "day of traffic" and note the class counts.
2. `--step train`: learn from 70% of traffic.
3. `--step evaluate`: measure on the unseen 30%.
4. `--step detect --live 15`: replay traffic as a monitoring feed.
5. `--step visualize`: build the dashboards.
6. Open `outputs/alerts.csv` and investigate the top attacker IPs as a SOC analyst would.
7. Try the API with a hand-crafted DoS flow (see section I).
8. *Stretch:* change `stealth_frac` to 0.6 and `N_FLOWS` to 100000 and compare results; discuss why performance drops.

**Graphs:** class distribution, attack timeline, behaviour boxplots, score histogram, confusion matrices, ROC, feature importance, alerts by severity, top attacker IPs, detected threats on timeline. **Anomalies to highlight:** the two daily burst windows, the top 3 source IPs, the Unknown Anomaly alerts.

---
## I. Execution
```
python main.py --step all
python main.py --step train          # only training
python main.py --step detect --live 15
python app.py
```
Test the API (new terminal):
```
curl -X POST http://127.0.0.1:5000/predict -H "Content-Type: application/json" -d "{\"duration\":0.1,\"protocol_type\":\"tcp\",\"service\":\"http\",\"src_bytes\":150,\"dst_bytes\":20,\"packets\":450,\"failed_logins\":0,\"request_rate\":500,\"unique_dst_ports\":1,\"syn_ratio\":0.95,\"conn_count_60s\":350}"
```
Expected: `{"predicted_type":"DoS","threat_detected":true,"threat_score":1.0}`. A normal HTTPS flow returns `threat_detected: false`.

**Successful run looks like:** 20,000 flows generated → ~99.8% test accuracy, recall ≈99% → ~1,270 alerts (≈1,128 CRITICAL) → 11 PNGs in `images/` and CSV/log files in `outputs/`.

---
## J. GitHub Upload Strategy
1. Install Git, then `git config --global user.name "Your Name"` and `git config --global user.email you@email.com`.
2. Create an empty repo on github.com (no README), named **AI-Cybersecurity-Threat-Detection**.
3. In the project folder:
```
git init
git add .
git commit -m "feat: project structure and setup"
git branch -M main
git remote add origin https://github.com/<you>/AI-Cybersecurity-Threat-Detection.git
git push -u origin main
```
4. Commit in small steps (see section L); use prefixes `feat:`, `fix:`, `docs:`, `chore:`.
5. Commit the PNGs in `images/` so README images render; for a demo video upload to YouTube (unlisted) or drag a short GIF/MP4 into the README editor on GitHub.
6. Polish: add a repo **description**, **topics**, pin the repo on your profile, add a LICENSE (MIT), and keep the README screenshots current.

**Description:** *ML-based network intrusion & anomaly detection with simulated DoS, brute-force and port-scan attacks, severity-ranked SOC alerts and a Flask API.*
**Topics:** `cybersecurity` `machine-learning` `intrusion-detection` `anomaly-detection` `random-forest` `isolation-forest` `scikit-learn` `python` `soc` `threat-detection` `flask` `data-science`

## K. README
Use the `README.md` in the project root as-is; replace `<your-username>` and add your own screenshots/demo link.

---
## L. Commit Plan (7 days)
| Day | Work | Commit message | Proof |
|---|---|---|---|
| 1 | folders, requirements, .gitignore, config | `chore: initialise project structure and environment` | terminal with `pip list`, repo tree |
| 2 | simulator + loader | `feat: add traffic and attack simulator` | `df.head()` screenshot, class counts |
| 3 | preprocess + features | `feat: add cleaning, feature engineering and pipeline` | cleaning log, new feature columns |
| 4 | train.py | `feat: train RF, LR, attack-type and Isolation Forest models` | training log, `models/` folder |
| 5 | evaluate.py | `feat: add evaluation metrics and plots` | `metrics.csv`, confusion matrix |
| 6 | detect + visualize + app | `feat: add alert engine, dashboards and Flask API` | alert feed, graphs, API response |
| 7 | README, images, polish, tag | `docs: add README, results and screenshots` then `git tag v1.0` | GitHub repo page screenshot |

## M. Proof Checklist (save in `images/`)
| # | Capture | File name |
|---|---|---|
| 1 | Dataset preview (`head()`, class counts) | `00_dataset_preview.png` |
| 2 | Preprocessing output (clean log, features) | `00_preprocessing_output.png` |
| 3 | Training logs | `00_training_logs.png` |
| 4 | Confusion matrix | `05_confusion_matrix.png` ✔ generated |
| 5 | Anomaly detection graph | `11_detected_anomalies.png` ✔ generated |
| 6 | Prediction / API response | `12_api_prediction.png` |
| 7 | Alert feed (final output) | `13_alert_feed.png` |
| 8 | GitHub repo preview | `14_github_repo.png` |

Show them in the README with `![Confusion matrix](images/05_confusion_matrix.png)`.

---
## Interview Quick-Prep
- **Why recall over accuracy?** Missing an attack costs more than a false alarm; accuracy is misleading with 80% normal traffic.
- **Why Isolation Forest?** It needs no attack labels and can flag novel behaviour.
- **What would you change with real data?** Use CICIDS2017/UNSW-NB15, a time-based split, SMOTE/threshold tuning, and drift monitoring.
- **Limitations:** simulated data is cleaner than real traffic; no live packet capture; thresholds are static.
