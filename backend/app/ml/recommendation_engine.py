"""
Rule-based recommendation engine.

Runs AFTER the ML model produces a risk_score/risk_level.
Checks individual indicator values against clinical thresholds
and generates structured, human-readable recommendations.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.ml.features import FeatureVector
from app.models.prediction import RiskLevel


def _flag(label: str, value: float, threshold: float, unit: str, direction: str = ">") -> str:
    op = ">" if direction == ">" else "<"
    return f"{label}: {value:.2f} {unit} ({op} {threshold} {unit})"


class RecommendationEngine:
    def generate(
        self,
        fv: FeatureVector,
        risk_score: float,
        risk_level: RiskLevel,
    ) -> dict:
        """
        Returns a dict with keys:
          summary, recommendations (list[dict]), warning_flags (list[str]), generated_at
        """
        warning_flags = self._collect_warnings(fv)
        recs = self._build_recommendations(fv, risk_level)
        summary = self._build_summary(risk_score, risk_level, warning_flags)

        return {
            "summary": summary,
            "recommendations": recs,
            "warning_flags": warning_flags,
            "generated_at": datetime.now(timezone.utc),
        }

    # ─── Warning flags ────────────────────────────────────────────────────────

    def _collect_warnings(self, fv: FeatureVector) -> list[str]:
        flags = []
        if fv.glucose is not None:
            if fv.glucose >= 7.0:
                flags.append(_flag("Глюкоза натощак", fv.glucose, 7.0, "ммоль/л"))
            elif fv.glucose >= 5.6:
                flags.append(_flag("Глюкоза натощак (предиабет)", fv.glucose, 5.6, "ммоль/л"))
        if fv.hba1c is not None:
            if fv.hba1c >= 6.5:
                flags.append(_flag("HbA1c", fv.hba1c, 6.5, "%"))
            elif fv.hba1c >= 5.7:
                flags.append(_flag("HbA1c (предиабет)", fv.hba1c, 5.7, "%"))
        if fv.homa_ir is not None and fv.homa_ir > 2.5:
            flags.append(_flag("HOMA-IR (инсулинорезистентность)", fv.homa_ir, 2.5, ""))
        if fv.bmi is not None and fv.bmi >= 30:
            flags.append(_flag("ИМТ (ожирение)", fv.bmi, 30, "кг/м²"))
        elif fv.bmi is not None and fv.bmi >= 25:
            flags.append(_flag("ИМТ (избыточный вес)", fv.bmi, 25, "кг/м²"))
        if fv.systolic_bp is not None and fv.systolic_bp >= 130:
            flags.append(_flag("АД систолическое", fv.systolic_bp, 130, "мм рт.ст."))
        if fv.triglycerides is not None and fv.triglycerides > 1.7:
            flags.append(_flag("Триглицериды", fv.triglycerides, 1.7, "ммоль/л"))
        if fv.hdl_cholesterol is not None and fv.hdl_cholesterol < 1.0:
            flags.append(_flag("ЛПВП (низкий)", fv.hdl_cholesterol, 1.0, "ммоль/л", "<"))
        return flags

    # ─── Recommendations ──────────────────────────────────────────────────────

    def _build_recommendations(
        self, fv: FeatureVector, risk_level: RiskLevel
    ) -> list[dict]:
        recs: list[dict] = []

        # Diagnostics
        if risk_level == RiskLevel.HIGH:
            recs.append({
                "category": "Диагностика",
                "text": (
                    "Рекомендуется проведение орального глюкозотолерантного теста (ОГТТ) "
                    "для верификации нарушения углеводного обмена."
                ),
                "priority": "HIGH",
            })
        if fv.glucose is not None and fv.glucose >= 5.6:
            recs.append({
                "category": "Диагностика",
                "text": "Контрольное определение глюкозы натощак через 3 месяца.",
                "priority": "HIGH" if fv.glucose >= 7.0 else "MEDIUM",
            })
        if fv.hba1c is None:
            recs.append({
                "category": "Диагностика",
                "text": "Определение HbA1c не было выполнено. Рекомендуется включить в следующее обследование.",
                "priority": "MEDIUM",
            })

        # Nutrition
        if fv.bmi is not None and fv.bmi >= 25:
            recs.append({
                "category": "Питание",
                "text": (
                    "Снижение калорийности рациона на 500–750 ккал/сут. "
                    "Ограничение быстрых углеводов, насыщенных жиров и сахаросодержащих напитков. "
                    "Увеличение доли овощей, цельнозерновых продуктов."
                ),
                "priority": "HIGH" if fv.bmi >= 30 else "MEDIUM",
            })
        if fv.triglycerides is not None and fv.triglycerides > 1.7:
            recs.append({
                "category": "Питание",
                "text": "Ограничение потребления простых углеводов и алкоголя для снижения уровня триглицеридов.",
                "priority": "MEDIUM",
            })

        # Physical activity
        if risk_level in (RiskLevel.MODERATE, RiskLevel.HIGH):
            recs.append({
                "category": "Физическая активность",
                "text": (
                    "Не менее 150 минут умеренной аэробной активности в неделю "
                    "(ходьба, плавание, велосипед). "
                    "Силовые тренировки 2–3 раза в неделю."
                ),
                "priority": "HIGH",
            })

        # Cardiovascular
        if fv.systolic_bp is not None and fv.systolic_bp >= 130:
            recs.append({
                "category": "Контроль АД",
                "text": (
                    "Артериальное давление превышает целевые значения. "
                    "Рекомендуется мониторинг АД и консультация кардиолога."
                ),
                "priority": "HIGH",
            })

        # Family history
        if fv.family_history:
            recs.append({
                "category": "Наследственный риск",
                "text": (
                    "Отягощённый семейный анамнез по сахарному диабету. "
                    "Рекомендуется скрининговое обследование 1 раз в год."
                ),
                "priority": "MEDIUM",
            })

        # Follow-up
        follow_up_months = {RiskLevel.LOW: 12, RiskLevel.MODERATE: 6, RiskLevel.HIGH: 3}
        recs.append({
            "category": "Повторное обследование",
            "text": (
                f"Рекомендуется повторное лабораторное обследование через "
                f"{follow_up_months[risk_level]} мес."
            ),
            "priority": "MEDIUM" if risk_level == RiskLevel.LOW else "HIGH",
        })

        return recs

    # ─── Summary ──────────────────────────────────────────────────────────────

    def _build_summary(
        self, risk_score: float, risk_level: RiskLevel, warning_flags: list[str]
    ) -> str:
        level_text = {
            RiskLevel.LOW: "низкий",
            RiskLevel.MODERATE: "умеренный",
            RiskLevel.HIGH: "высокий",
        }[risk_level]

        summary = (
            f"По результатам ML-анализа лабораторных показателей определён "
            f"{level_text} риск сахарного диабета 2 типа "
            f"(вероятность: {risk_score * 100:.1f}%). "
        )
        if warning_flags:
            summary += (
                f"Выявлены {len(warning_flags)} клинически значимых отклонения. "
            )
        summary += (
            "Представленный анализ носит вспомогательный характер. "
            "Окончательное заключение принимает лечащий врач."
        )
        return summary


recommendation_engine = RecommendationEngine()
