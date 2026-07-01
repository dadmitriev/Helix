import enum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    DOCTOR = "DOCTOR"
    LABORATORIAN = "LABORATORIAN"
    PATIENT = "PATIENT"


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="userrole"), nullable=False)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ─── Relationships ────────────────────────────────────────────────────────
    patient_card: Mapped["Patient | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Patient",
        foreign_keys="Patient.user_id",
        back_populates="user",
        uselist=False,
    )
    created_patients: Mapped[list["Patient"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Patient",
        foreign_keys="Patient.created_by",
        back_populates="creator",
    )
    doctor_orders: Mapped[list["LabOrder"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "LabOrder",
        foreign_keys="LabOrder.ordering_doctor_id",
        back_populates="ordering_doctor",
    )
    lab_orders_handled: Mapped[list["LabOrder"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "LabOrder",
        foreign_keys="LabOrder.laboratorian_id",
        back_populates="laboratorian",
    )
    conclusions: Mapped[list["DoctorConclusion"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "DoctorConclusion",
        back_populates="doctor",
    )

    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)
