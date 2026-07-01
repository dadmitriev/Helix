import enum
from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    # Links to system user account (nullable — patient may exist without account)
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    medical_record_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[Gender] = mapped_column(Enum(Gender, name="gender"), nullable=False)

    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    family_history_diabetes: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ─── Relationships ────────────────────────────────────────────────────────
    user: Mapped["User | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        foreign_keys=[user_id],
        back_populates="patient_card",
    )
    creator: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        foreign_keys=[created_by],
        back_populates="created_patients",
    )
    lab_orders: Mapped[list["LabOrder"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "LabOrder",
        back_populates="patient",
        order_by="LabOrder.ordered_at.desc()",
    )

    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)

    @property
    def age(self) -> int:
        from datetime import date as dt_date
        today = dt_date.today()
        born = self.date_of_birth
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
