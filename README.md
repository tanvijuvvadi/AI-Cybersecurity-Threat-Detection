# 🛡️ AI-Powered Cybersecurity Threat Detection

A machine-learning system that analyses network traffic, **detects attacks (DoS, Brute Force, Port Scan, and unknown anomalies)**, assigns a severity, and generates SOC-style alerts, built end to end on a **simulated network environment**.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-orange) ![License](https://img.shields.io/badge/License-MIT-green)

## 📌 Problem Statement
Rule-based security tools (static firewalls, signature IDS) miss new and low-and-slow attacks and drown analysts in false alerts. This project uses ML to learn what *normal* traffic looks like and flag malicious behaviour automatically.

## 🏢 Industry Relevance
The same ideas power Network Intrusion Detection (NIDS), SIEM/SOC analytics, bank fraud monitoring and UEBA at companies such as Microsoft, Google, IBM Security and Palo Alto Networks. This repo is a small-scale replica of that pipeline.

## 🧰 Tech Stack
Python · Pandas · NumPy · Scikit-learn (Random Forest, Logistic Regression, Isolation Forest) · Matplotlib · Seaborn · Flask (optional API) · Git/GitHub

## 🏗️ Architecture
```
Traffic logs ─► Cleaning ─► Feature engineering ─► Pipeline (scale + encode)
                                                        │
              ┌─────────────────────────────────────────┼───────────────────────┐
              ▼                                         ▼                       ▼
     Random Forest (attack?)               Attack-type classifier      Isolation Forest (unusual?)
              └──────────────► Detection engine + severity + evidence ◄─────────┘
                                          │
                              alerts.csv / alerts.log / dashboards / Flask API
```

## 📊 Dataset
`src/simulate_data.py` generates 20,000 flows (80% normal, 8% DoS, 6% Brute Force, 6% Port Scan) with realistic attack signatures, attacker IP pools, attack bursts over 24 h, and 35% *stealthy* attacks that mimic normal traffic.
It can also load **NSL-KDD / CICIDS2017 / UNSW-NB15** through `src/data_loader.py::load_real_dataset`.

## ⚙️ Installation
```bash
git clone https://github.com/<your-username>/AI-Cybersecurity-Threat-Detection.git
cd AI-Cybersecurity-Threat-Detection
python -m venv venv
venv\Scripts\activate          # Windows   |   source venv/bin/activate  (Mac/Linux)
pip install -r requirements.txt
```

## ▶️ How to Run
```bash
python main.py --step all          # simulate → train → evaluate → detect → visualize
python main.py --step detect --live 15   # replay a live alert feed
python app.py                      # optional REST API on http://127.0.0.1:5000/predict
```

## 📈 Results (unseen 6,000-flow test set)
| Model | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| Logistic Regression | 0.9985 | 0.9967 | 0.9958 | 0.9962 |
| Random Forest | 0.9985 | 0.9992 | 0.9933 | 0.9962 |
| Isolation Forest (unsupervised, trained on normal only) | 0.9683 | 0.9346 | 0.9050 | 0.9196 |

> ⚠️ **Honest note:** simulated attacks are cleaner than real ones, so scores on CICIDS2017 / UNSW-NB15 will be lower (typically 95–99% with more false positives). Reporting that gap is a strength in interviews.

Sample alert:
```
[CRITICAL] 2026-01-01 00:32:26 DoS  203.0.113.3 -> 10.0.0.2  score=1.00 | request rate 524/s; SYN ratio 0.77
```

## 🖼️ Screenshots
| Class distribution | Attack timeline |
|---|---|
| ![](images/01_class_distribution.png) | ![](images/02_attack_timeline.png) |
| **Confusion matrix** | **Feature importance** |
| ![](images/05_confusion_matrix.png) | ![](images/08_feature_importance.png) |
| **Detected threats** | **Alerts by severity** |
| ![](images/11_detected_anomalies.png) | ![](images/09_alerts_by_severity.png) |

## 📂 Project Structure
```
├── main.py              # one-command pipeline runner
├── app.py               # Flask prediction API
├── src/                 # config, simulate_data, data_loader, preprocess, features, train, evaluate, detect, visualize
├── data/ models/ outputs/ images/ docs/ notebooks/
└── requirements.txt
```

## 🎓 Learning Outcomes
Network-traffic feature engineering · leakage-free ML pipelines · handling class imbalance · supervised vs unsupervised detection · precision/recall trade-offs in security · alert severity design · serving a model via API · professional Git workflow.

## 🔮 Future Work
Real datasets (CICIDS2017), SMOTE and hyper-parameter tuning, streaming with Kafka, Streamlit dashboard, SIEM (Splunk/ELK) integration, deep-learning autoencoders.

## 📄 License
MIT
