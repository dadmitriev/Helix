"""
Clinical reference ranges used by the recommendation engine
and for highlighting abnormal values in the UI.

Sources: ADA Clinical Practice Guidelines 2024, WHO Diabetes criteria.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ReferenceRange:
    low: Optional[float]   # None = no lower bound
    high: Optional[float]  # None = no upper bound
    unit: str
    label_ru: str


REFERENCE_RANGES: dict[str, ReferenceRange] = {
    "glucose": ReferenceRange(
        low=3.9, high=5.6, unit="ммоль/л",
        label_ru="Глюкоза натощак"
    ),
    "hba1c": ReferenceRange(
        low=None, high=5.7, unit="%",
        label_ru="HbA1c"
    ),
    "insulin": ReferenceRange(
        low=2.0, high=25.0, unit="мкЕд/мл",
        label_ru="Инсулин натощак"
    ),
    "bmi": ReferenceRange(
        low=18.5, high=24.9, unit="кг/м²",
        label_ru="ИМТ"
    ),
    "systolic_bp": ReferenceRange(
        low=None, high=130, unit="мм рт.ст.",
        label_ru="АД систолическое"
    ),
    "diastolic_bp": ReferenceRange(
        low=None, high=80, unit="мм рт.ст.",
        label_ru="АД диастолическое"
    ),
    "total_cholesterol": ReferenceRange(
        low=None, high=5.0, unit="ммоль/л",
        label_ru="Общий холестерин"
    ),
    "hdl_cholesterol": ReferenceRange(
        low=1.0, high=None, unit="ммоль/л",
        label_ru="ЛПВП"
    ),
    "ldl_cholesterol": ReferenceRange(
        low=None, high=3.0, unit="ммоль/л",
        label_ru="ЛПНП"
    ),
    "triglycerides": ReferenceRange(
        low=None, high=1.7, unit="ммоль/л",
        label_ru="Триглицериды"
    ),
    "waist_circumference": ReferenceRange(
        low=None, high=94.0, unit="см",
        label_ru="Окружность талии (муж.)"
    ),
    "homa_ir": ReferenceRange(
        low=None, high=2.5, unit="",
        label_ru="HOMA-IR"
    ),
}


def is_abnormal(field: str, value: float) -> bool:
    ref = REFERENCE_RANGES.get(field)
    if not ref or value is None:
        return False
    if ref.low is not None and value < ref.low:
        return True
    if ref.high is not None and value > ref.high:
        return True
    return False


def get_abnormal_fields(values: dict) -> list[str]:
    return [f for f, v in values.items() if v is not None and is_abnormal(f, float(v))]
