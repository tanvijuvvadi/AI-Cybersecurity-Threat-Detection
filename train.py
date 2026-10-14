"""Train: (1) supervised binary detectors, (2) attack-type classifier, (3) unsupervised Isolation Forest."""
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from src import config
from src.data_loader import load_simulated
from src.features import add_features
from src.preprocess import build_preprocessor, clean, split_xy


def make_pipeline(X, estimator):
    return Pipeline([("prep", build_preprocessor(X)), ("model", estimator)])


def run():
    config.ensure_dirs()
    df = add_features(clean(load_simulated()))

    # Stratified split: the test set is kept aside as "unseen live traffic"
    train, test = train_test_split(df, test_size=0.3, stratify=df["attack_type"],
                                   random_state=config.RANDOM_STATE)
    train.to_csv(config.TRAIN_FILE, index=False)
    test.to_csv(config.TEST_FILE, index=False)
    print(f"[train] train={len(train):,}  test={len(test):,}")

    X_train, y_train = split_xy(train)

    # 1) supervised binary detectors (class_weight handles the 80/20 imbalance)
    models = {
        "logistic_regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "random_forest": RandomForestClassifier(n_estimators=150, class_weight="balanced",
                                                n_jobs=-1, random_state=config.RANDOM_STATE),
    }
    for name, est in models.items():
        pipe = make_pipeline(X_train, est).fit(X_train, y_train)
        joblib.dump(pipe, config.MODELS / f"{name}.joblib")
        print(f"[train] saved {name}")

    # 2) multi-class: WHICH attack is it?
    _, y_type = split_xy(train, target="attack_type")
    clf = make_pipeline(X_train, RandomForestClassifier(n_estimators=150, class_weight="balanced",
                                                        n_jobs=-1, random_state=config.RANDOM_STATE))
    joblib.dump(clf.fit(X_train, y_type), config.MODELS / "attack_type_classifier.joblib")
    print("[train] saved attack_type_classifier")

    # 3) unsupervised: learn ONLY what normal looks like, flag anything unusual (finds unknown attacks)
    X_normal = X_train[y_train == 0]
    iso = make_pipeline(X_train, IsolationForest(n_estimators=200, contamination=0.02,
                                                 random_state=config.RANDOM_STATE))
    joblib.dump(iso.fit(X_normal), config.MODELS / "isolation_forest.joblib")
    print("[train] saved isolation_forest (trained on normal traffic only)")


if __name__ == "__main__":
    run()
