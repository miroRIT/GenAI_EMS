from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from emergencypulse.domain.models import AmbulanceStatus, IncidentSeverity


class Base(DeclarativeBase):
    pass


class AmbulanceRecord(Base):
    __tablename__ = "ambulances"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    call_sign: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    status: Mapped[AmbulanceStatus] = mapped_column(
        Enum(AmbulanceStatus, name="ambulance_status"), nullable=False, index=True
    )
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    equipment_level: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class IncidentRecord(Base):
    __tablename__ = "incidents"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    severity: Mapped[IncidentSeverity] = mapped_column(
        Enum(IncidentSeverity, name="incident_severity"), nullable=False
    )
    patient_latitude: Mapped[float] = mapped_column(nullable=False)
    patient_longitude: Mapped[float] = mapped_column(nullable=False)
    destination_latitude: Mapped[float | None] = mapped_column(nullable=True)
    destination_longitude: Mapped[float | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_ambulance_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    eta_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
