"""
Train the diabetes risk model and save the artifact.

Pipeline:
  1. Load synthetic dataset (or Pima Indians if available)
  2. Preprocess: impute → scale
  3. Train XGBClassifier
  4. Evaluate on hold-out set
  5. Save artifact: {"pipeline": sklearn.Pipeline, "model_name": str, "version": str}

Run from backend/:
    python -m ml_training.train
"""

import json
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

DATA_PATH = Path(__file__).parent / "data" / "synthetic_diabetes.csv"
MODELS_DIR = Path(__file__).parent.parent / "app" / "ml" / "models"
MODEL_VERSION = "1.0.0"
MODEL_NAME = "xgboost_v1"
OUTPUT_PATH = MODELS_DIR / "pipeline_v1.joblib"
METRICS_PATH = MODELS_DIR / "metrics_v1.json"

FEATURE_COLS = [
    "glucose", "hba1c", "insulin", "bmi", "age",
    "gender_male", "family_history",
    "systolic_bp", "diastolic_bp",
    "triglycerides", "hdl_cholesterol",
    "waist_circumference", "homa_ir",
]
TARGET_COL = "label"


def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        print(f"Data file not found: {DATA_PATH}")
        print("Run: python -m ml_training.generate_synthetic_data")
        sys.exit(1)
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} samples from {DATA_PATH}")
    return df


def build_pipeline(scale_pos_weight: float) -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("classifier", XGBClassifier(
            n_estimators=80,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_pos_weight,
            eval_metric="logloss",
            random_state=42,
            n_jobs=1,
        )),
    ])


def train() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data()
    # Use a subset for faster training on low-resource machines
    if len(df) > 2000:
        df = df.sample(n=2000, random_state=42)
        print(f"Using 2000 samples for training (reduced for performance)")

    X = df[FEATURE_COLS].values
    y = df[TARGET_COL].values

    neg, pos = (y == 0).sum(), (y == 1).sum()
    scale_pos_weight = neg / pos
    print(f"Class balance — negative: {neg}, positive: {pos}, scale_pos_weight: {scale_pos_weight:.2f}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    pipeline = build_pipeline(scale_pos_weight)

    print("Skipping cross-validation for faster training...")

    # ── Final training on full train set ──────────────────────────────────────
    print("Training final model...")
    pipeline.fit(X_train, y_train)

    # ── Evaluation on hold-out test set ───────────────────────────────────────
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]
    roc_auc = roc_auc_score(y_test, y_proba)

    print(f"\nTest set ROC-AUC: {roc_auc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["No Diabetes", "Diabetes"]))

    # ── Feature importances ───────────────────────────────────────────────────
    classifier = pipeline.named_steps["classifier"]
    importances = dict(zip(FEATURE_COLS, classifier.feature_importances_))
    top = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    print("\nTop feature importances:")
    for feat, imp in top[:8]:
        print(f"  {feat:25s}: {imp:.4f}")

    # ── Save artifact ─────────────────────────────────────────────────────────
    artifact = {
        "pipeline": pipeline,
        "model_name": MODEL_NAME,
        "version": MODEL_VERSION,
        "feature_names": FEATURE_COLS,
    }
    joblib.dump(artifact, OUTPUT_PATH)
    print(f"\nModel saved: {OUTPUT_PATH}")

    metrics = {
        "model_name": MODEL_NAME,
        "version": MODEL_VERSION,
        "test_roc_auc": float(roc_auc),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "feature_importances": {k: float(v) for k, v in importances.items()},
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Metrics saved: {METRICS_PATH}")


if __name__ == "__main__":
    train()
