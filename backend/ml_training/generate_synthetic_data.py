"""
Generate synthetic diabetes risk dataset.

Statistical distributions are based on:
- ADA Clinical Practice Guidelines (2024)
- WHO diabetes criteria
- Pima Indians Diabetes Dataset reference statistics

Run: python -m ml_training.generate_synthetic_data
Output: ml_training/data/synthetic_diabetes.csv
"""

import os
import numpy as np
import pandas as pd

SEED = 42
N_SAMPLES = 8000
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data", "synthetic_diabetes.csv")


def generate(n: int = N_SAMPLES, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # ── Demographics ──────────────────────────────────────────────────────────
    age = rng.integers(18, 80, size=n).astype(float)
    gender_male = rng.integers(0, 2, size=n).astype(float)
    family_history = (rng.random(n) < 0.30).astype(float)

    # ── Base risk — determines whether the sample is diabetic ─────────────────
    # High-risk features: older age, overweight, family history
    base_risk = (
        0.03 * (age - 40) / 40
        + 0.15 * family_history
        + rng.normal(0, 0.1, n)
    )
    base_risk = np.clip(base_risk, 0, 1)
    # Stratified: ~35% diabetic label
    label = (rng.random(n) < (0.20 + 0.45 * base_risk)).astype(int)

    # ── BMI ───────────────────────────────────────────────────────────────────
    bmi_base = rng.normal(27, 5, n)
    bmi = np.where(label == 1, bmi_base + rng.normal(4, 2, n), bmi_base)
    bmi = np.clip(bmi, 15, 55)

    # ── Waist circumference ───────────────────────────────────────────────────
    waist = 60 + 0.8 * bmi + rng.normal(0, 8, n) + 5 * label
    waist = np.clip(waist, 50, 150)

    # ── Glucose (fasting) ─────────────────────────────────────────────────────
    glucose_base = rng.normal(5.0, 0.8, n)
    glucose = np.where(label == 1, glucose_base + rng.normal(2.5, 1.2, n), glucose_base)
    glucose = np.clip(glucose, 2.5, 20.0)

    # ── HbA1c ─────────────────────────────────────────────────────────────────
    hba1c_base = rng.normal(5.3, 0.4, n)
    hba1c = np.where(label == 1, hba1c_base + rng.normal(1.5, 0.6, n), hba1c_base)
    hba1c = np.clip(hba1c, 3.5, 15.0)

    # ── Insulin ───────────────────────────────────────────────────────────────
    insulin_base = rng.lognormal(2.5, 0.5, n)  # log-normal distribution
    insulin = np.where(label == 1, insulin_base * rng.uniform(1.3, 2.5, n), insulin_base)
    insulin = np.clip(insulin, 1.0, 200.0)

    # ── HOMA-IR (calculated) ──────────────────────────────────────────────────
    homa_ir = (glucose * insulin) / 22.5

    # ── Blood pressure ────────────────────────────────────────────────────────
    systolic_bp = rng.normal(120, 15, n) + 10 * label + 0.2 * (age - 40)
    systolic_bp = np.clip(systolic_bp, 80, 210).astype(int)
    diastolic_bp = rng.normal(78, 10, n) + 5 * label
    diastolic_bp = np.clip(diastolic_bp, 50, 130).astype(int)

    # ── Lipids ────────────────────────────────────────────────────────────────
    triglycerides_base = rng.lognormal(0.4, 0.4, n)
    triglycerides = np.where(label == 1, triglycerides_base * 1.4, triglycerides_base)
    triglycerides = np.clip(triglycerides, 0.4, 10.0)

    hdl_base = rng.normal(1.4, 0.3, n)
    hdl = np.where(label == 1, hdl_base - rng.uniform(0.1, 0.4, n), hdl_base)
    hdl = np.clip(hdl, 0.3, 3.0)

    # ── Introduce realistic missingness ──────────────────────────────────────
    def mask(arr: np.ndarray, p: float) -> np.ndarray:
        masked = arr.astype(float).copy()
        masked[rng.random(n) < p] = np.nan
        return masked

    df = pd.DataFrame({
        "glucose": glucose,
        "hba1c": hba1c,
        "insulin": mask(insulin, 0.25),   # insulin often not ordered
        "bmi": bmi,
        "age": age,
        "gender_male": gender_male,
        "family_history": family_history,
        "systolic_bp": mask(systolic_bp.astype(float), 0.15),
        "diastolic_bp": mask(diastolic_bp.astype(float), 0.15),
        "triglycerides": mask(triglycerides, 0.20),
        "hdl_cholesterol": mask(hdl, 0.20),
        "waist_circumference": mask(waist, 0.30),
        "homa_ir": mask(homa_ir, 0.30),
        "label": label,
    })

    return df


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df = generate()
    df.to_csv(OUTPUT_PATH, index=False)

    diabetic = df["label"].sum()
    print(f"Generated {len(df)} samples:")
    print(f"  Diabetic:     {diabetic} ({diabetic/len(df)*100:.1f}%)")
    print(f"  Non-diabetic: {len(df)-diabetic} ({(len(df)-diabetic)/len(df)*100:.1f}%)")
    print(f"Saved to: {OUTPUT_PATH}")
