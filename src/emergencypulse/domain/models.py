from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class IncidentSeverity(StrEnum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class RoutePriority(StrEnum):
    emergency = "emergency"
    urgent = "urgent"
    routine = "routine"


class AmbulanceStatus(StrEnum):
    available = "available"
    assigned = "assigned"
    offline = "offline"


class Coordinate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class Ambulance(BaseModel):
    id: UUID
    call_sign: str = Field(..., min_length=2, max_length=32)
    status: AmbulanceStatus
    location: Coordinate
    equipment_level: int = Field(..., ge=1, le=5)


class IncidentCreate(BaseModel):
    patient_location: Coordinate
    destination: Coordinate | None = None
    severity: IncidentSeverity
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("notes")
    @classmethod
    def strip_notes(cls, value: str | None) -> str | None:
        return value.strip() if value else value


class RouteCalculationRequest(BaseModel):
    origin: Coordinate
    destination: Coordinate
    priority: RoutePriority = RoutePriority.emergency
    include_alternatives: bool = True
    use_signal_priority: bool = True
    traffic_level: float = Field(
        default=1.0,
        ge=0.5,
        le=2.5,
        description="Traffic multiplier supplied by an upstream traffic service.",
    )


class RouteSegment(BaseModel):
    start: Coordinate
    end: Coordinate
    distance_meters: int
    estimated_seconds: int
    instruction: str


class BestRouteResponse(BaseModel):
    estimated_distance_meters: int
    estimated_duration_seconds: int
    traffic_adjusted_duration_seconds: int
    signal_delay_seconds: int
    priority_savings_seconds: int
    route_polyline: list[Coordinate]
    segments: list[RouteSegment]
    alternatives: list["BestRouteResponse"] = Field(default_factory=list)
    rationale: str


class RoutePlan(BaseModel):
    ambulance_id: UUID
    incident_id: UUID
    estimated_arrival_seconds: int
    estimated_transport_seconds: int | None = None
    distance_to_patient_meters: int
    total_score: float
    route_polyline: list[Coordinate]
    rationale: str


class DispatchDecision(BaseModel):
    incident_id: UUID = Field(default_factory=uuid4)
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    severity: IncidentSeverity
    selected_route: RoutePlan
    alternatives: list[RoutePlan]
