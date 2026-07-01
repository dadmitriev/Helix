"""
Feature extraction from a LabOrder + Patient record
into the numeric vector expected by the ML pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.lab_order import LabOrder


# Ordered feature names — must match the training pipeline's column order
FEATURE_NAMES = [
    "glucose",
    "hba1c",
    "insulin",
    "bmi",
    "age",
    "gender_male",
    "family_history",
    "systolic_bp",
    "diastolic_bp",
    "triglycerides",
    "hdl_cholesterol",
    "waist_circumference",
    "homa_ir",
]

# Minimum required features for a valid prediction
MIN_REQUIRED_FEATURES = {"glucose", "hba1c", "bmi"}


@dataclass
class FeatureVector:
    glucose: float | None
    hba1c: float | None
    insulin: float | None
    bmi: float | None
    age: int
    gender_male: int          # 1 = male, 0 = female
    family_history: int       # 1 = yes, 0 = no
    systolic_bp: float | None
    diastolic_bp: float | None
    triglycerides: float | None
    hdl_cholesterol: float | None
    waist_circumference: float | None
    homa_ir: float | None

    def to_dict(self) -> dict[str, float | None]:
        return {name: getattr(self, name) for name in FEATURE_NAMES}

    def to_list(self) -> list[float | None]:
        return [getattr(self, name) for name in FEATURE_NAMES]


def _to_float(v) -> float | None:
    if v is None:
        return None
    return float(v)


def compute_homa_ir(glucose: float | None, insulin: float | None) -> float | None:
    """HOMA-IR = (fasting glucose [mmol/L] × fasting insulin [µU/mL]) / 22.5"""
    if glucose is None or insulin is None:
        return None
    return round((glucose * insulin) / 22.5, 3)


def extract_features(order: "LabOrder") -> FeatureVector:
    """Build a FeatureVector from a LabOrder (results must be filled)."""
    patient = order.patient
    glucose = _to_float(order.glucose)
    insulin = _to_float(order.insulin)
    homa_ir = compute_homa_ir(glucose, insulin)

    return FeatureVector(
        glucose=glucose,
        hba1c=_to_float(order.hba1c),
        insulin=insulin,
        bmi=_to_float(order.bmi),
        age=patient.age,
        gender_male=1 if patient.gender.value == "MALE" else 0,
        family_history=1 if patient.family_history_diabetes else 0,
        systolic_bp=_to_float(order.systolic_bp),
        diastolic_bp=_to_float(order.diastolic_bp),
        triglycerides=_to_float(order.triglycerides),
        hdl_cholesterol=_to_float(order.hdl_cholesterol),
        waist_circumference=_to_float(order.waist_circumference),
        homa_ir=homa_ir,
    )


def validate_features(fv: FeatureVector) -> list[str]:
    """Return list of missing minimum-required feature names."""
    missing = []
    for feat in MIN_REQUIRED_FEATURES:
        if getattr(fv, feat) is None:
            missing.append(feat)
    return missing
