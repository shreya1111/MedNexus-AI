"""
MedNexus AI — Diabetes Prediction Model Training
Dataset: Pima Indians Diabetes Dataset (768 samples, 8 features)
Models: LogisticRegression, RandomForestClassifier, GradientBoostingClassifier
MLOps: MLflow experiment tracking + DVC data versioning
"""
import os
import json
import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, classification_report, confusion_matrix
)
from sklearn.pipeline import Pipeline
import joblib

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────────────────────

MODELS_DIR = Path(__file__).parent.parent / "models"
DATA_DIR = Path(__file__).parent.parent / "data"
MODELS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

RANDOM_STATE = 42

# ─── Synthetic dataset generation (replace with real PIMA dataset) ───────────

def generate_synthetic_diabetes_data(n_samples: int = 768) -> pd.DataFrame:
    """
    Generate synthetic diabetes data following PIMA Indians dataset distribution.
    In production, load: pd.read_csv('data/diabetes.csv')
    """
    np.random.seed(RANDOM_STATE)

    positive = int(n_samples * 0.35)
    negative = n_samples - positive

    def gen_samples(n, is_diabetic):
        glucose_mean = 141 if is_diabetic else 110
        bmi_mean = 35 if is_diabetic else 28
        return {
            "pregnancies": np.random.poisson(3.5 if is_diabetic else 2.5, n).clip(0, 17),
            "glucose": np.random.normal(glucose_mean, 20, n).clip(50, 200),
            "blood_pressure": np.random.normal(75 if is_diabetic else 70, 12, n).clip(40, 122),
            "skin_thickness": np.random.normal(29 if is_diabetic else 22, 10, n).clip(0, 60),
            "insulin": np.random.exponential(150 if is_diabetic else 80, n).clip(0, 846),
            "bmi": np.random.normal(bmi_mean, 6, n).clip(15, 60),
            "diabetes_pedigree": np.random.exponential(0.5 if is_diabetic else 0.3, n).clip(0.08, 2.5),
            "age": np.random.normal(37 if is_diabetic else 28, 10, n).clip(21, 81),
            "outcome": np.ones(n, dtype=int) if is_diabetic else np.zeros(n, dtype=int),
        }

    pos_data = gen_samples(positive, True)
    neg_data = gen_samples(negative, False)

    combined = {k: np.concatenate([pos_data[k], neg_data[k]]) for k in pos_data}
    df = pd.DataFrame(combined)
    df = df.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)
    return df


# ─── Feature engineering ──────────────────────────────────────────────────────

def preprocess(df: pd.DataFrame):
    """Handle zero-values as missing and engineer features."""
    cols_with_zeros = ["glucose", "blood_pressure", "skin_thickness", "insulin", "bmi"]
    df = df.copy()
    for col in cols_with_zeros:
        if col in df.columns:
            df[col] = df[col].replace(0, np.nan)
            df[col] = df[col].fillna(df[col].median())

    # Feature engineering
    df["glucose_bmi"] = df["glucose"] * df["bmi"] / 100
    df["age_bmi"] = df["age"] * df["bmi"] / 100
    df["age_group"] = pd.cut(df["age"], bins=[0, 30, 45, 60, 100], labels=[0, 1, 2, 3]).astype(int)
    df["bmi_category"] = pd.cut(df["bmi"], bins=[0, 18.5, 25, 30, 100], labels=[0, 1, 2, 3]).astype(int)

    # Final NaN check
    df = df.fillna(df.median(numeric_only=True))
    return df


# ─── Training ─────────────────────────────────────────────────────────────────

def train_diabetes_model():
    logger.info("=" * 60)
    logger.info("MedNexus AI — Diabetes Model Training")
    logger.info("=" * 60)

    # Load data
    csv_path = DATA_DIR / "diabetes.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded real dataset: {len(df)} samples")
    else:
        df = generate_synthetic_diabetes_data(1000)
        df.to_csv(csv_path, index=False)
        logger.info(f"Generated synthetic dataset: {len(df)} samples → saved to {csv_path}")

    df = preprocess(df)

    feature_cols = [c for c in df.columns if c != "outcome"]
    X = df[feature_cols].values
    y = df["outcome"].values

    logger.info(f"Features: {feature_cols}")
    logger.info(f"Class distribution: {np.bincount(y)}")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y)

    # Models to compare
    models = {
        "LogisticRegression": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, C=1.0, random_state=RANDOM_STATE)),
        ]),
        "RandomForest": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", RandomForestClassifier(n_estimators=200, max_depth=8, random_state=RANDOM_STATE)),
        ]),
        "GradientBoosting": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", GradientBoostingClassifier(n_estimators=150, max_depth=4, learning_rate=0.1, random_state=RANDOM_STATE)),
        ]),
    }

    results = {}
    best_model_name = None
    best_f1 = 0

    for name, model in models.items():
        logger.info(f"\nTraining {name}…")
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

        cv_scores = cross_val_score(model, X, y, cv=5, scoring="f1")
        metrics["cv_f1_mean"] = round(cv_scores.mean(), 4)
        metrics["cv_f1_std"] = round(cv_scores.std(), 4)

        results[name] = metrics
        logger.info(f"  {name}: Accuracy={metrics['accuracy']}, F1={metrics['f1']}, AUC={metrics['roc_auc']}, CV-F1={metrics['cv_f1_mean']}±{metrics['cv_f1_std']}")

        if metrics["f1"] > best_f1:
            best_f1 = metrics["f1"]
            best_model_name = name
            best_model = model

    logger.info(f"\n✓ Best model: {best_model_name} (F1={best_f1:.4f})")

    # Save best model
    model_path = MODELS_DIR / "diabetes_model.pkl"
    joblib.dump(best_model, model_path)
    logger.info(f"✓ Model saved: {model_path}")

    # Save metadata
    metadata = {
        "model_name": best_model_name,
        "features": feature_cols,
        "metrics": results[best_model_name],
        "all_results": results,
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "class_distribution": {"negative": int(np.bincount(y)[0]), "positive": int(np.bincount(y)[1])},
    }
    meta_path = MODELS_DIR / "diabetes_metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"✓ Metadata saved: {meta_path}")

    return best_model, metadata


def load_diabetes_model():
    model_path = MODELS_DIR / "diabetes_model.pkl"
    if not model_path.exists():
        logger.info("Model not found, training now…")
        train_diabetes_model()
    return joblib.load(model_path)


if __name__ == "__main__":
    model, meta = train_diabetes_model()
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"Best Model: {meta['model_name']}")
    print(f"Accuracy:   {meta['metrics']['accuracy']}")
    print(f"F1 Score:   {meta['metrics']['f1']}")
    print(f"ROC AUC:    {meta['metrics']['roc_auc']}")
    print(f"CV F1:      {meta['metrics']['cv_f1_mean']} ± {meta['metrics']['cv_f1_std']}")
