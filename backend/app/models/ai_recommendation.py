from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    prediction_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("predictions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Short human-readable summary
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    # Structured list: [{"category": str, "text": str, "priority": "HIGH"|"MEDIUM"|"LOW"}, ...]
    recommendations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Flags for clinically critical values, e.g. ["Глюкоза > 7.0 ммоль/л"]
    warning_flags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # ─── Relationships ────────────────────────────────────────────────────────
    prediction: Mapped["Prediction"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Prediction", back_populates="ai_recommendation"
    )
