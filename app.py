"""Optional real-time API:  python app.py   then POST /predict  (needs `pip install flask`)."""
import joblib
import pandas as pd
from flask import Flask, jsonify, request
from src import config
from src.features import add_features

app = Flask(__name__)
rf = joblib.load(config.MODELS / "random_forest.joblib")
clf = joblib.load(config.MODELS / "attack_type_classifier.joblib")

FIELDS = ["duration", "protocol_type", "service", "src_bytes", "dst_bytes", "packets", "failed_logins",
          "request_rate", "unique_dst_ports", "syn_ratio", "conn_count_60s"]


@app.post("/predict")
def predict():
    data = request.get_json()
    missing = [f for f in FIELDS if f not in data]
    if missing:
        return jsonify({"error": f"missing fields: {missing}"}), 400
    X = add_features(pd.DataFrame([{f: data[f] for f in FIELDS}]))
    score = float(rf.predict_proba(X)[0, 1])
    return jsonify({"threat_detected": score >= 0.5, "threat_score": round(score, 4),
                    "predicted_type": str(clf.predict(X)[0])})


if __name__ == "__main__":
    app.run(debug=True)
