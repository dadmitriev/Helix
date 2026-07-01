import enum
from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.prediction import RiskLevel


class ConclusionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"


class DoctorConclusion(Base):
    __tablename__ = "doctor_conclusions"

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
    doctor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Preliminary diagnosis text (not a legal diagnosis — for support purposes only)
    preliminary_diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Full doctor's conclusion text
    conclusion_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Doctor's recommendations (may be edited from AI suggestions)
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Did the doctor agree with the AI risk assessment?
    agreed_with_ai: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Doctor's final risk level (may differ from ML prediction)
    risk_confirmed: Mapped[RiskLevel | None] = mapped_column(
        Enum(RiskLevel, name="risklevel"), nullable=True
    )

    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[ConclusionStatus] = mapped_column(
        Enum(ConclusionStatus, name="conclusionstatus"),
        default=ConclusionStatus.DRAFT,
        nullable=False,
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ─── Relationships ────────────────────────────────────────────────────────
    lab_order: Mapped["LabOrder"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "LabOrder", back_populates="conclusion"
    )
    doctor: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", back_populates="conclusions"
    )
