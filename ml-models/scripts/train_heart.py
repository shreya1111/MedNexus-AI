"""
MedNexus AI — Heart Disease Prediction Model Training
Dataset: Cleveland Heart Disease Dataset (303 samples, 13 features)
Models: RandomForest, GradientBoosting, SVM
"""
import os
import json
import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.pipeline import Pipeline
import joblib

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent / "models"
DATA_DIR = Path(__file__).parent.parent / "data"
MODELS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
RANDOM_STATE = 42


def generate_synthetic_heart_data(n_samples: int = 800) -> pd.DataFrame:
    np.random.seed(RANDOM_STATE)
    positive = int(n_samples * 0.46)
    negative = n_samples - positive

    def gen(n, has_disease):
        return {
            "age": np.random.normal(56 if has_disease else 52, 9, n).clip(29, 77),
            "sex": np.random.choice([0, 1], n, p=[0.3, 0.7] if has_disease else [0.4, 0.6]),
            "chest_pain_type": np.random.choice([0,1,2,3], n, p=[0.5,0.2,0.2,0.1] if has_disease else [0.1,0.3,0.3,0.3]),
            "blood_pressure": np.random.normal(135 if has_disease else 128, 18, n).clip(94, 200),
            "cholesterol": np.random.normal(251 if has_disease else 242, 50, n).clip(126, 564),
            "fasting_blood_sugar": np.random.choice([0, 1], n, p=[0.8, 0.2] if has_disease else [0.85, 0.15]),
            "resting_ecg": np.random.choice([0,1,2], n, p=[0.4,0.4,0.2] if has_disease else [0.5,0.4,0.1]),
            "max_heart_rate": np.random.normal(139 if has_disease else 158, 23, n).clip(71, 202),
            "exercise_angina": np.random.choice([0, 1], n, p=[0.4, 0.6] if has_disease else [0.8, 0.2]),
            "st_depression": np.random.exponential(1.5 if has_disease else 0.6, n).clip(0, 6.2),
            "st_slope": np.random.choice([0,1,2], n, p=[0.5,0.3,0.2] if has_disease else [0.2,0.5,0.3]),
            "major_vessels": np.random.choice([0,1,2,3], n, p=[0.3,0.3,0.2,0.2] if has_disease else [0.6,0.2,0.1,0.1]),
            "thalassemia": np.random.choice([1,2,3], n, p=[0.1,0.6,0.3] if has_disease else [0.1,0.3,0.6]),
            "target": np.ones(n, dtype=int) if has_disease else np.zeros(n, dtype=int),
        }

    pos = gen(positive, True)
    neg = gen(negative, False)
    combined = {k: np.concatenate([pos[k], neg[k]]) for k in pos}
    df = pd.DataFrame(combined)
    return df.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["age_chol"] = df["age"] * df["cholesterol"] / 1000
    df["hr_age_ratio"] = df["max_heart_rate"] / df["age"]
    df["bp_category"] = pd.cut(df["blood_pressure"], bins=[0, 120, 130, 140, 200], labels=[0,1,2,3]).astype(int)
    return df


def train_heart_model():
    logger.info("=" * 60)
    logger.info("MedNexus AI — Heart Disease Model Training")
    logger.info("=" * 60)

    csv_path = DATA_DIR / "heart_disease.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded real dataset: {len(df)} samples")
    else:
        df = generate_synthetic_heart_data(800)
        df.to_csv(csv_path, index=False)
        logger.info(f"Generated synthetic dataset: {len(df)} samples")

    df = preprocess(df)
    feature_cols = [c for c in df.columns if c != "target"]
    X = df[feature_cols].values
    y = df["target"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y)

    models = {
        "RandomForest": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", RandomForestClassifier(n_estimators=200, max_depth=8, random_state=RANDOM_STATE)),
        ]),
        "GradientBoosting": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", GradientBoostingClassifier(n_estimators=150, learning_rate=0.1, random_state=RANDOM_STATE)),
        ]),
        "SVM": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", SVC(probability=True, kernel="rbf", C=1.0, random_state=RANDOM_STATE)),
        ]),
    }

    results = {}
    best_name, best_f1, best_model = None, 0.0, None

    for name, model in models.items():
        logger.info(f"Training {name}…")
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        metrics = {
            "accuracy": round(accuracy_score(y_test, y_pred), 4),
            "precision": round(precision_score(y_test, y_pred), 4),
            "recall": round(recall_score(y_test, y_pred), 4),
            "f1": round(f1_score(y_test, y_pred), 4),
            "roc_auc": round(roc_auc_score(y_test, y_prob), 4),
        }
        cv = cross_val_score(model, X, y, cv=5, scoring="f1")
        metrics["cv_f1_mean"] = round(cv.mean(), 4)
        results[name] = metrics
        logger.info(f"  {name}: F1={metrics['f1']}, AUC={metrics['roc_auc']}, CV-F1={metrics['cv_f1_mean']}")
        if metrics["f1"] > best_f1:
            best_f1, best_name, best_model = metrics["f1"], name, model

    logger.info(f"Best model: {best_name} (F1={best_f1:.4f})")
    model_path = MODELS_DIR / "heart_model.pkl"
    joblib.dump(best_model, model_path)

    metadata = {"model_name": best_name, "features": feature_cols, "metrics": results[best_name], "all_results": results}
    with open(MODELS_DIR / "heart_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    return best_model, metadata


if __name__ == "__main__":
    model, meta = train_heart_model()
    print(f"\nBest: {meta['model_name']} | F1={meta['metrics']['f1']} | AUC={meta['metrics']['roc_auc']}")
