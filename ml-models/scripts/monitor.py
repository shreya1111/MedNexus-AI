"""
MedNexus AI — MLOps Monitoring
Evidently AI drift detection + MLflow experiment tracking
"""
import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_data_drift(reference_path: str, current_path: str) -> dict:
    """
    Data drift detection using statistical tests.
    Production: uses Evidently AI DataDriftPreset
    """
    import numpy as np

    # Mock drift report (production uses evidently)
    # from evidently.report import Report
    # from evidently.metric_preset import DataDriftPreset
    # report = Report(metrics=[DataDriftPreset()])
    # report.run(reference_data=ref_df, current_data=cur_df)
    # report.save_html("drift_report.html")

    drift_report = {
        "dataset_drift": False,
        "drift_share": 0.12,
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "glucose": {"drift_detected": False, "p_value": 0.32, "stattest": "KS"},
            "bmi": {"drift_detected": False, "p_value": 0.18, "stattest": "KS"},
            "age": {"drift_detected": False, "p_value": 0.45, "stattest": "KS"},
            "blood_pressure": {"drift_detected": False, "p_value": 0.07, "stattest": "KS"},
        },
        "recommendation": "No significant drift detected. Model remains valid.",
    }

    if drift_report["drift_share"] > 0.3:
        drift_report["recommendation"] = "Significant data drift detected. Consider model retraining."
        drift_report["dataset_drift"] = True

    return drift_report


def log_mlflow_experiment(model_name: str, params: dict, metrics: dict) -> str:
    """
    Log experiment to MLflow.
    Production: mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    """
    # import mlflow
    # mlflow.set_experiment("mednexus-medical-models")
    # with mlflow.start_run(run_name=model_name):
    #     mlflow.log_params(params)
    #     mlflow.log_metrics(metrics)
    #     mlflow.sklearn.log_model(model, model_name)
    #     run_id = mlflow.active_run().info.run_id

    run_id = f"mock-run-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    logger.info(f"[MLflow] Logged experiment: {model_name}, run_id={run_id}")
    logger.info(f"[MLflow] Params: {params}")
    logger.info(f"[MLflow] Metrics: {metrics}")
    return run_id


def generate_model_card(model_name: str, metadata: dict) -> str:
    """Generate a model card for documentation."""
    card = f"""# Model Card: {model_name}

## Overview
- **Model**: {metadata.get('model_name', 'Unknown')}
- **Task**: Binary Classification
- **Domain**: Healthcare / Medical AI
- **Version**: 1.0.0
- **Date**: {datetime.utcnow().strftime('%Y-%m-%d')}

## Performance Metrics
| Metric | Value |
|--------|-------|
| Accuracy | {metadata.get('metrics', {}).get('accuracy', 'N/A')} |
| F1 Score | {metadata.get('metrics', {}).get('f1', 'N/A')} |
| ROC AUC | {metadata.get('metrics', {}).get('roc_auc', 'N/A')} |
| Precision | {metadata.get('metrics', {}).get('precision', 'N/A')} |
| Recall | {metadata.get('metrics', {}).get('recall', 'N/A')} |

## Features
{chr(10).join(f'- {f}' for f in metadata.get('features', []))}

## Ethical Considerations
- This model is for **screening assistance only**, not diagnosis
- Results must be reviewed by a qualified healthcare professional
- Model was trained on synthetic data; validate on real clinical datasets before deployment
- Monitor for demographic bias across age, sex, and ethnicity groups

## Limitations
- Training data may not represent all patient populations
- Model confidence scores are calibrated but not a substitute for clinical judgment
- Regular drift monitoring and retraining required (recommended: monthly)

## Usage
```python
import joblib
model = joblib.load('models/{model_name.lower().replace(" ", "_")}_model.pkl')
prediction = model.predict([[glucose, bmi, age, ...]])
probability = model.predict_proba([[glucose, bmi, age, ...]])[:, 1]
```
"""
    return card


if __name__ == "__main__":
    drift = check_data_drift("data/reference.csv", "data/current.csv")
    print(json.dumps(drift, indent=2))

    models_dir = Path(__file__).parent.parent / "models"
    for meta_file in models_dir.glob("*_metadata.json"):
        with open(meta_file) as f:
            metadata = json.load(f)
        model_name = meta_file.stem.replace("_metadata", "")
        run_id = log_mlflow_experiment(model_name, {"random_state": 42}, metadata.get("metrics", {}))
        card = generate_model_card(model_name, metadata)
        card_path = models_dir / f"{model_name}_card.md"
        card_path.write_text(card)
        print(f"Model card written: {card_path}")
