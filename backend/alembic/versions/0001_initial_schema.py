"""Initial schema — all tables

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enums ─────────────────────────────────────────────────────────────────
    op.execute("CREATE TYPE userrole AS ENUM ('ADMIN','DOCTOR','LABORATORIAN','PATIENT')")
    op.execute("CREATE TYPE gender AS ENUM ('MALE','FEMALE')")
    op.execute("CREATE TYPE laborderstatus AS ENUM ('ORDERED','IN_PROGRESS','RESULTS_READY','CONCLUDED')")
    op.execute("CREATE TYPE laborderpriority AS ENUM ('ROUTINE','URGENT','EMERGENCY')")
    op.execute("CREATE TYPE risklevel AS ENUM ('LOW','MODERATE','HIGH')")
    op.execute("CREATE TYPE conclusionstatus AS ENUM ('DRAFT','SENT')")

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("ADMIN", "DOCTOR", "LABORATORIAN", "PATIENT", name="userrole"), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("middle_name", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── patients ──────────────────────────────────────────────────────────────
    op.create_table(
        "patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("medical_record_number", sa.String(50), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("middle_name", sa.String(100), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("gender", sa.Enum("MALE", "FEMALE", name="gender"), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("family_history_diabetes", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_patients_mrn", "patients", ["medical_record_number"], unique=True)

    # ── lab_orders ────────────────────────────────────────────────────────────
    op.create_table(
        "lab_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("ordering_doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("laboratorian_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.Enum("ORDERED", "IN_PROGRESS", "RESULTS_READY", "CONCLUDED", name="laborderstatus"), nullable=False),
        sa.Column("priority", sa.Enum("ROUTINE", "URGENT", "EMERGENCY", name="laborderpriority"), nullable=False),
        sa.Column("requested_panels", postgresql.JSONB(), nullable=False),
        sa.Column("order_notes", sa.Text(), nullable=True),
        sa.Column("ordered_at", sa.DateTime(timezone=True), nullable=False),
        # Results
        sa.Column("analysis_date", sa.Date(), nullable=True),
        sa.Column("analysis_time", sa.Time(), nullable=True),
        sa.Column("lab_notes", sa.Text(), nullable=True),
        sa.Column("results_submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("glucose", sa.Numeric(5, 2), nullable=True),
        sa.Column("hba1c", sa.Numeric(4, 2), nullable=True),
        sa.Column("insulin", sa.Numeric(6, 2), nullable=True),
        sa.Column("bmi", sa.Numeric(5, 2), nullable=True),
        sa.Column("waist_circumference", sa.Numeric(5, 1), nullable=True),
        sa.Column("systolic_bp", sa.Integer(), nullable=True),
        sa.Column("diastolic_bp", sa.Integer(), nullable=True),
        sa.Column("total_cholesterol", sa.Numeric(5, 2), nullable=True),
        sa.Column("hdl_cholesterol", sa.Numeric(5, 2), nullable=True),
        sa.Column("ldl_cholesterol", sa.Numeric(5, 2), nullable=True),
        sa.Column("triglycerides", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_lab_orders_patient_id", "lab_orders", ["patient_id"])
    op.create_index("ix_lab_orders_doctor_id", "lab_orders", ["ordering_doctor_id"])
    op.create_index("ix_lab_orders_status", "lab_orders", ["status"])

    # ── predictions ───────────────────────────────────────────────────────────
    op.create_table(
        "predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lab_order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("risk_score", sa.Numeric(5, 4), nullable=False),
        sa.Column("risk_level", sa.Enum("LOW", "MODERATE", "HIGH", name="risklevel"), nullable=False),
        sa.Column("homa_ir", sa.Numeric(6, 3), nullable=True),
        sa.Column("feature_importances", postgresql.JSONB(), nullable=False),
        sa.Column("raw_output", postgresql.JSONB(), nullable=False),
        sa.Column("predicted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_predictions_lab_order_id", "predictions", ["lab_order_id"], unique=True)

    # ── ai_recommendations ────────────────────────────────────────────────────
    op.create_table(
        "ai_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("recommendations", postgresql.JSONB(), nullable=False),
        sa.Column("warning_flags", postgresql.JSONB(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── doctor_conclusions ────────────────────────────────────────────────────
    op.create_table(
        "doctor_conclusions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lab_order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("preliminary_diagnosis", sa.Text(), nullable=True),
        sa.Column("conclusion_text", sa.Text(), nullable=False),
        sa.Column("recommendations", sa.Text(), nullable=True),
        sa.Column("agreed_with_ai", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("risk_confirmed", sa.Enum("LOW", "MODERATE", "HIGH", name="risklevel"), nullable=True),
        sa.Column("follow_up_date", sa.Date(), nullable=True),
        sa.Column("status", sa.Enum("DRAFT", "SENT", name="conclusionstatus"), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_doctor_conclusions_lab_order_id", "doctor_conclusions", ["lab_order_id"], unique=True)

    # ── audit_logs ────────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("doctor_conclusions")
    op.drop_table("ai_recommendations")
    op.drop_table("predictions")
    op.drop_table("lab_orders")
    op.drop_table("patients")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS conclusionstatus")
    op.execute("DROP TYPE IF EXISTS risklevel")
    op.execute("DROP TYPE IF EXISTS laborderpriority")
    op.execute("DROP TYPE IF EXISTS laborderstatus")
    op.execute("DROP TYPE IF EXISTS gender")
    op.execute("DROP TYPE IF EXISTS userrole")
