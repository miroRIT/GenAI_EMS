"""initial schema with PostGIS support

Revision ID: 20260704_0001
Revises:
Create Date: 2026-07-04
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260704_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE TYPE ambulance_status AS ENUM ('available', 'assigned', 'offline')")
    op.execute("CREATE TYPE incident_severity AS ENUM ('critical', 'high', 'medium', 'low')")
    op.create_table(
        "ambulances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("call_sign", sa.String(length=32), nullable=False, unique=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "available",
                "assigned",
                "offline",
                name="ambulance_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("equipment_level", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "severity",
            postgresql.ENUM(
                "critical",
                "high",
                "medium",
                "low",
                name="incident_severity",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("patient_latitude", sa.Float(), nullable=False),
        sa.Column("patient_longitude", sa.Float(), nullable=False),
        sa.Column("destination_latitude", sa.Float(), nullable=True),
        sa.Column("destination_longitude", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("assigned_ambulance_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("eta_seconds", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.execute(
        """
        ALTER TABLE ambulances
        ADD COLUMN location geography(Point, 4326)
        GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography) STORED
        """
    )
    op.execute(
        """
        ALTER TABLE incidents
        ADD COLUMN patient_location geography(Point, 4326)
        GENERATED ALWAYS AS (
            ST_SetSRID(ST_MakePoint(patient_longitude, patient_latitude), 4326)::geography
        ) STORED
        """
    )
    op.create_index("ix_ambulances_status", "ambulances", ["status"])
    op.create_index("ix_ambulances_location", "ambulances", ["location"], postgresql_using="gist")
    op.create_index(
        "ix_incidents_patient_location",
        "incidents",
        ["patient_location"],
        postgresql_using="gist",
    )

    op.execute(
        """
        INSERT INTO ambulances (id, call_sign, status, latitude, longitude, equipment_level)
        VALUES
          ('11111111-1111-1111-1111-111111111111', 'MEDIC-01', 'available', 40.7580, -73.9855, 5),
          ('22222222-2222-2222-2222-222222222222', 'MEDIC-02', 'available', 40.7306, -73.9352, 4),
          ('33333333-3333-3333-3333-333333333333', 'BLS-03', 'available', 40.7060, -74.0086, 3)
        """
    )


def downgrade() -> None:
    op.drop_index("ix_incidents_patient_location", table_name="incidents")
    op.drop_index("ix_ambulances_location", table_name="ambulances")
    op.drop_index("ix_ambulances_status", table_name="ambulances")
    op.drop_table("incidents")
    op.drop_table("ambulances")
    op.execute("DROP TYPE IF EXISTS incident_severity")
    op.execute("DROP TYPE IF EXISTS ambulance_status")
