"""
Evaluate saved model on the test dataset and print detailed metrics.

Useful for model validation and thesis appendix tables.
Run from backend/:
    python -m ml_training.evaluate
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    classification_report,
    confusion_matrix,
    roc_auc_score,
    average_precision_score,
    f1_score,
)
from sklearn.model_selection import train_test_split

DATA_PATH = Path(__file__).parent / "data" / "synthetic_diabetes.csv"
MODEL_PATH = Path(__file__).parent.parent / "app" / "ml" / "models" / "pipeline_v1.joblib"

FEATURE_COLS = [
    "glucose", "hba1c", "insulin", "bmi", "age",
    "gender_male", "family_history",
    "systolic_bp", "diastolic_bp",
    "triglycerides", "hdl_cholesterol",
    "waist_circumference", "homa_ir",
]


def evaluate() -> None:
    if not MODEL_PATH.exists():
        print(f"Model not found: {MODEL_PATH}")
        print("Run: python -m ml_training.train")
        return

    artifact = joblib.load(MODEL_PATH)
    pipeline = artifact["pipeline"]
    print(f"Loaded model: {artifact['model_name']} v{artifact['version']}")

    df = pd.read_csv(DATA_PATH)
    X = df[FEATURE_COLS].values
    y = df["label"].values

    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    print(f"\n{'='*50}")
    print("EVALUATION RESULTS")
    print(f"{'='*50}")
    print(f"Test samples:      {len(y_test)}")
    print(f"Positive (label=1): {y_test.sum()} ({y_test.mean()*100:.1f}%)")
    print(f"\nROC-AUC:           {roc_auc_score(y_test, y_proba):.4f}")
    print(f"Average Precision: {average_precision_score(y_test, y_proba):.4f}")
    print(f"F1 (macro):        {f1_score(y_test, y_pred, average='macro'):.4f}")
    print(f"\n{classification_report(y_test, y_pred, target_names=['No Diabetes', 'Diabetes'])}")

    cm = confusion_matrix(y_test, y_pred)
    print("Confusion Matrix:")
    print(f"  TN={cm[0,0]:4d}  FP={cm[0,1]:4d}")
    print(f"  FN={cm[1,0]:4d}  TP={cm[1,1]:4d}")

    sensitivity = cm[1, 1] / (cm[1, 1] + cm[1, 0])
    specificity = cm[0, 0] / (cm[0, 0] + cm[0, 1])
    print(f"\nSensitivity (Recall): {sensitivity:.4f}")
    print(f"Specificity:          {specificity:.4f}")


if __name__ == "__main__":
    evaluate()
