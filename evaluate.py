"""Evaluate all models on unseen test traffic; save metrics tables and plots."""
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             f1_score, precision_score, recall_score, roc_auc_score, roc_curve)
from src import config
from src.preprocess import split_xy


def _load(name):
    return joblib.load(config.MODELS / f"{name}.joblib")


def iso_predict(iso, X):
    """IsolationForest returns -1 for anomaly -> convert to 1 = attack, 0 = normal."""
    return (iso.predict(X) == -1).astype(int)


def run():
    test = pd.read_csv(config.TEST_FILE)
    X, y = split_xy(test)
    rows, probs = [], {}

    for name in ["logistic_regression", "random_forest"]:
        m = _load(name)
        pred, prob = m.predict(X), m.predict_proba(X)[:, 1]
        probs[name] = prob
        rows.append([name, accuracy_score(y, pred), precision_score(y, pred),
                     recall_score(y, pred), f1_score(y, pred), roc_auc_score(y, prob)])
    iso = _load("isolation_forest")
    pred = iso_predict(iso, X)
    rows.append(["isolation_forest (unsupervised)", accuracy_score(y, pred), precision_score(y, pred),
                 recall_score(y, pred), f1_score(y, pred), roc_auc_score(y, -iso.decision_function(X))])

    metrics = pd.DataFrame(rows, columns=["model", "accuracy", "precision", "recall", "f1", "roc_auc"]).round(4)
    metrics.to_csv(config.OUTPUTS / "metrics.csv", index=False)
    print("\n=== MODEL COMPARISON (unseen test data) ===")
    print(metrics.to_string(index=False))

    # --- confusion matrix (binary, Random Forest) ---
    rf = _load("random_forest")
    cm = confusion_matrix(y, rf.predict(X))
    plt.figure(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["Normal", "Attack"],
                yticklabels=["Normal", "Attack"])
    plt.title("Random Forest - Confusion Matrix"); plt.xlabel("Predicted"); plt.ylabel("Actual")
    plt.tight_layout(); plt.savefig(config.IMAGES / "05_confusion_matrix.png", dpi=150); plt.close()

    # --- ROC curves ---
    plt.figure(figsize=(5.5, 4.5))
    for n, p in probs.items():
        fpr, tpr, _ = roc_curve(y, p)
        plt.plot(fpr, tpr, label=n)
    plt.plot([0, 1], [0, 1], "k--", alpha=.4)
    plt.xlabel("False Positive Rate"); plt.ylabel("True Positive Rate"); plt.title("ROC Curves"); plt.legend()
    plt.tight_layout(); plt.savefig(config.IMAGES / "06_roc_curves.png", dpi=150); plt.close()

    # --- attack-type confusion matrix ---
    clf = _load("attack_type_classifier")
    _, y_type = split_xy(test, target="attack_type")
    pt = clf.predict(X)
    labels = sorted(y_type.unique())
    report = classification_report(y_type, pt, digits=4)
    (config.OUTPUTS / "classification_report.txt").write_text(report)
    print("\n=== ATTACK-TYPE CLASSIFICATION REPORT ===\n" + report)
    plt.figure(figsize=(6, 5))
    sns.heatmap(confusion_matrix(y_type, pt, labels=labels), annot=True, fmt="d", cmap="Purples",
                xticklabels=labels, yticklabels=labels)
    plt.title("Attack-Type Confusion Matrix"); plt.xlabel("Predicted"); plt.ylabel("Actual")
    plt.tight_layout(); plt.savefig(config.IMAGES / "07_attack_type_confusion.png", dpi=150); plt.close()

    # --- feature importance ---
    names = rf.named_steps["prep"].get_feature_names_out()
    imp = pd.Series(rf.named_steps["model"].feature_importances_, index=names).nlargest(12).sort_values()
    plt.figure(figsize=(7, 5)); imp.plot(kind="barh", color="teal")
    plt.title("Top 12 Features - Random Forest"); plt.tight_layout()
    plt.savefig(config.IMAGES / "08_feature_importance.png", dpi=150); plt.close()
    print("[evaluate] plots saved to images/")


if __name__ == "__main__":
    run()
