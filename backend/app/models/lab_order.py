import enum
from datetime import date, datetime, time, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LabOrderStatus(str, enum.Enum):
    ORDERED = "ORDERED"
    IN_PROGRESS = "IN_PROGRESS"
    RESULTS_READY = "RESULTS_READY"
    CONCLUDED = "CONCLUDED"


class LabOrderPriority(str, enum.Enum):
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    EMERGENCY = "EMERGENCY"


# Valid panel codes — defines which fields belong to each panel
PANEL_FIELD_MAP: dict[str, list[str]] = {
    "GLUCOSE": ["glucose"],
    "HBA1C": ["hba1c"],
    "INSULIN": ["insulin"],
    "LIPID_PANEL": ["total_cholesterol", "hdl_cholesterol", "ldl_cholesterol", "triglycerides"],
    "BLOOD_PRESSURE": ["systolic_bp", "diastolic_bp"],
    "ANTHROPOMETRY": ["bmi", "waist_circumference"],
}

ALL_PANELS = list(PANEL_FIELD_MAP.keys())


class LabOrder(Base):
    __tablename__ = "lab_orders"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # ─── Order metadata (created by doctor) ───────────────────────────────────
    patient_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True
    )
    ordering_doctor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    laboratorian_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    status: Mapped[LabOrderStatus] = mapped_column(
        Enum(LabOrderStatus, name="laborderstatus"),
        default=LabOrderStatus.ORDERED,
        nullable=False,
        index=True,
    )
    priority: Mapped[LabOrderPriority] = mapped_column(
        Enum(LabOrderPriority, name="laborderpriority"),
        default=LabOrderPriority.ROUTINE,
        nullable=False,
    )

    # List of panel codes, e.g. ["GLUCOSE", "HBA1C", "LIPID_PANEL"]
    requested_panels: Mapped[list] = mapped_column(JSONB, nullable=False)
    order_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    ordered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ─── Results (filled by laboratorian) ─────────────────────────────────────
    analysis_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    analysis_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    lab_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    results_submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Blood glucose and related
    glucose: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    hba1c: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    insulin: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)

    # Anthropometry
    bmi: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    waist_circumference: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)

    # Blood pressure
    systolic_bp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    diastolic_bp: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Lipid panel
    total_cholesterol: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    hdl_cholesterol: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    ldl_cholesterol: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    triglycerides: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    # ─── Relationships ────────────────────────────────────────────────────────
    patient: Mapped["Patient"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Patient", back_populates="lab_orders"
    )
    ordering_doctor: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        foreign_keys=[ordering_doctor_id],
        back_populates="doctor_orders",
    )
    laboratorian: Mapped["User | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        foreign_keys=[laboratorian_id],
        back_populates="lab_orders_handled",
    )
    prediction: Mapped["Prediction | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Prediction",
        back_populates="lab_order",
        uselist=False,
        cascade="all, delete-orphan",
    )
    conclusion: Mapped["DoctorConclusion | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "DoctorConclusion",
        back_populates="lab_order",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def get_required_fields(self) -> list[str]:
        """Return all field names required by requested_panels."""
        fields: list[str] = []
        for panel in self.requested_panels:
            fields.extend(PANEL_FIELD_MAP.get(panel, []))
        return list(dict.fromkeys(fields))  # deduplicate, preserve order

    def get_missing_fields(self) -> list[str]:
        """Return required fields that are currently None."""
        return [f for f in self.get_required_fields() if getattr(self, f) is None]
