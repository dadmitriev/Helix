import enum
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    lab_order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("lab_orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)

    risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, name="risklevel"), nullable=False
    )

    # Calculated auxiliary index
    homa_ir: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)

    # {feature_name: importance_value, ...}
    feature_importances: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Full raw output from the model pipeline for reproducibility
    raw_output: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    predicted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # ─── Relationships ────────────────────────────────────────────────────────
    lab_order: Mapped["LabOrder"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "LabOrder", back_populates="prediction"
    )
    ai_recommendation: Mapped["AIRecommendation | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "AIRecommendation",
        back_populates="prediction",
        uselist=False,
        cascade="all, delete-orphan",
    )
