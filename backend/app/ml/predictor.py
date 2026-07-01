"""
DiabetesRiskPredictor — singleton loaded at application startup.

Wraps the scikit-learn Pipeline (preprocessor + XGBClassifier) stored by ml_training/train.py.
Exposes a single `predict(order)` method that returns a structured result
ready to be persisted as Prediction + AIRecommendation.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import joblib
import numpy as np

from app.core.config import settings
from app.core.exceptions import InsufficientDataError, MLModelNotReadyError
from app.ml.features import FeatureVector, extract_features, validate_features
from app.ml.recommendation_engine import recommendation_engine
from app.models.prediction import RiskLevel

if TYPE_CHECKING:
    from app.models.lab_order import LabOrder

logger = logging.getLogger(__name__)

# Risk thresholds (configurable)
RISK_THRESHOLDS = {
    RiskLevel.LOW: (0.0, 0.35),
    RiskLevel.MODERATE: (0.35, 0.65),
    RiskLevel.HIGH: (0.65, 1.01),
}


def _score_to_level(score: float) -> RiskLevel:
    for level, (low, high) in RISK_THRESHOLDS.items():
        if low <= score < high:
            return level
    return RiskLevel.HIGH


class DiabetesRiskPredictor:
    def __init__(self) -> None:
        self._pipeline = None
        self._model_name: str = ""
        self._model_version: str = ""

    def load(self, model_path: str | None = None) -> None:
        path = Path(model_path or settings.ml_model_path)
        if not path.exists():
            logger.warning(
                "ML model not found at %s. "
                "Run ml_training/train.py to generate the model. "
                "Prediction endpoint will be unavailable.",
                path,
            )
            return

        try:
            artifact = joblib.load(path)
            self._pipeline = artifact["pipeline"]
            self._model_name = artifact.get("model_name", "xgboost")
            self._model_version = artifact.get("version", "unknown")
            logger.info(
                "ML model loaded: %s v%s from %s",
                self._model_name, self._model_version, path,
            )
        except Exception as exc:
            logger.error("Failed to load ML model: %s", exc)

    @property
    def is_ready(self) -> bool:
        return self._pipeline is not None

    def predict(self, order: "LabOrder") -> dict:
        """
        Run prediction for a LabOrder (results must be filled).

        Returns a dict with keys:
          prediction_data, recommendation_data
        """
        if not self.is_ready:
            raise MLModelNotReadyError()

        fv: FeatureVector = extract_features(order)

        missing = validate_features(fv)
        if missing:
            raise InsufficientDataError(
                f"Missing required fields for prediction: {', '.join(missing)}"
            )

        feature_dict = fv.to_dict()
        X = np.array([[v if v is not None else np.nan for v in fv.to_list()]])

        proba = self._pipeline.predict_proba(X)[0]
        risk_score = float(proba[1])  # probability of class 1 (diabetes)
        risk_level = _score_to_level(risk_score)

        feature_importances = self._get_feature_importances(X)

        recommendation_data = recommendation_engine.generate(fv, risk_score, risk_level)

        prediction_data = {
            "model_name": self._model_name,
            "model_version": self._model_version,
            "risk_score": round(risk_score, 4),
            "risk_level": risk_level,
            "homa_ir": fv.homa_ir,
            "feature_importances": feature_importances,
            "raw_output": {
                "proba_class_0": float(proba[0]),
                "proba_class_1": float(proba[1]),
                "features_used": feature_dict,
            },
            "predicted_at": datetime.now(timezone.utc),
        }

        return {"prediction_data": prediction_data, "recommendation_data": recommendation_data}

    def _get_feature_importances(self, X: np.ndarray) -> dict[str, float]:
        """Extract feature importances using SHAP if available, else model importances."""
        from app.ml.features import FEATURE_NAMES

        try:
            import shap
            # XGBClassifier is nested inside the pipeline
            classifier = self._pipeline.named_steps.get("classifier") or self._pipeline[-1]
            preprocessor = self._pipeline[:-1]
            X_transformed = preprocessor.transform(X)

            explainer = shap.TreeExplainer(classifier)
            shap_values = explainer.shap_values(X_transformed)
            # For binary classification, shap_values may be list[array] or array
            if isinstance(shap_values, list):
                values = shap_values[1][0]
            else:
                values = shap_values[0]

            importances = {name: round(abs(float(v)), 4) for name, v in zip(FEATURE_NAMES, values)}
        except Exception:
            # Fallback: use built-in feature importances
            try:
                classifier = self._pipeline[-1]
                raw = classifier.feature_importances_
                importances = {
                    name: round(float(v), 4)
                    for name, v in zip(FEATURE_NAMES, raw)
                }
            except Exception:
                importances = {}

        # Sort descending by importance
        return dict(sorted(importances.items(), key=lambda x: x[1], reverse=True))


# Module-level singleton
predictor = DiabetesRiskPredictor()
