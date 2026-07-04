from math import asin, cos, radians, sin, sqrt
from uuid import uuid4

from emergencypulse.domain.models import (
    Ambulance,
    BestRouteResponse,
    Coordinate,
    DispatchDecision,
    IncidentCreate,
    IncidentSeverity,
    RouteCalculationRequest,
    RoutePlan,
    RoutePriority,
    RouteSegment,
)
from emergencypulse.repositories.ambulance_repository import AmbulanceRepository

EARTH_RADIUS_METERS = 6_371_000
URBAN_AMBULANCE_METERS_PER_SECOND = 13.9

SEVERITY_WEIGHT = {
    IncidentSeverity.critical: 0.72,
    IncidentSeverity.high: 0.56,
    IncidentSeverity.medium: 0.38,
    IncidentSeverity.low: 0.24,
}

PRIORITY_SIGNAL_SAVINGS = {
    RoutePriority.emergency: 0.7,
    RoutePriority.urgent: 0.45,
    RoutePriority.routine: 0.0,
}


class NoAmbulanceAvailableError(Exception):
    pass


def haversine_meters(origin: Coordinate, destination: Coordinate) -> float:
    lat1 = radians(origin.latitude)
    lon1 = radians(origin.longitude)
    lat2 = radians(destination.latitude)
    lon2 = radians(destination.longitude)
    d_lat = lat2 - lat1
    d_lon = lon2 - lon1
    a = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lon / 2) ** 2
    return 2 * EARTH_RADIUS_METERS * asin(sqrt(a))


class RoutingService:
    def __init__(self, repository: AmbulanceRepository | None = None) -> None:
        self.repository = repository

    async def dispatch(self, incident: IncidentCreate) -> DispatchDecision:
        if self.repository is None:
            raise RuntimeError("Dispatch requires an ambulance repository")
        ambulances = await self.repository.list_available()
        if not ambulances:
            raise NoAmbulanceAvailableError("No available ambulances are online")

        incident_id = uuid4()
        plans = [
            self._score_ambulance(ambulance, incident, incident_id) for ambulance in ambulances
        ]
        plans.sort(key=lambda plan: plan.total_score)
        selected = plans[0]
        record = await self.repository.persist_dispatch(incident, selected)

        return DispatchDecision(
            incident_id=record.id,
            severity=incident.severity,
            selected_route=selected.model_copy(update={"incident_id": record.id}),
            alternatives=[
                plan.model_copy(update={"incident_id": record.id}) for plan in plans[1:4]
            ],
        )

    def calculate_best_route(self, request: RouteCalculationRequest) -> BestRouteResponse:
        return self._calculate_route_variant(
            origin=request.origin,
            destination=request.destination,
            priority=request.priority,
            traffic_level=request.traffic_level,
            use_signal_priority=request.use_signal_priority,
            variant_name="fastest",
            detour_factor=1.0,
            include_alternatives=request.include_alternatives,
        )

    def _score_ambulance(
        self, ambulance: Ambulance, incident: IncidentCreate, incident_id
    ) -> RoutePlan:
        distance = haversine_meters(ambulance.location, incident.patient_location)
        traffic_multiplier = self._traffic_multiplier(ambulance.location, incident.patient_location)
        signal_penalty = self._signal_penalty_seconds(distance)
        eta = int(
            (distance / URBAN_AMBULANCE_METERS_PER_SECOND) * traffic_multiplier + signal_penalty
        )
        transport_seconds = None
        if incident.destination:
            transport_distance = haversine_meters(incident.patient_location, incident.destination)
            transport_seconds = int(
                (transport_distance / URBAN_AMBULANCE_METERS_PER_SECOND) * traffic_multiplier
                + self._signal_penalty_seconds(transport_distance)
            )

        equipment_bonus = max(0, ambulance.equipment_level - 3) * 12
        score = eta - equipment_bonus - (SEVERITY_WEIGHT[incident.severity] * 30)
        return RoutePlan(
            ambulance_id=ambulance.id,
            incident_id=incident_id,
            estimated_arrival_seconds=max(1, eta),
            estimated_transport_seconds=transport_seconds,
            distance_to_patient_meters=int(distance),
            total_score=round(score, 2),
            route_polyline=[ambulance.location, incident.patient_location],
            rationale="Lowest weighted ETA after traffic, signal timing, and capability scoring.",
        )

    def _traffic_multiplier(self, origin: Coordinate, destination: Coordinate) -> float:
        density_proxy = abs(origin.latitude - destination.latitude) + abs(
            origin.longitude - destination.longitude
        )
        return min(1.75, 1.05 + density_proxy * 10)

    def _signal_penalty_seconds(self, distance_meters: float) -> int:
        estimated_intersections = max(1, int(distance_meters / 350))
        return min(90, estimated_intersections * 4)

    def _calculate_route_variant(
        self,
        origin: Coordinate,
        destination: Coordinate,
        priority: RoutePriority,
        traffic_level: float,
        use_signal_priority: bool,
        variant_name: str,
        detour_factor: float,
        include_alternatives: bool,
    ) -> BestRouteResponse:
        base_distance = haversine_meters(origin, destination)
        distance = int(base_distance * detour_factor)
        uncongested_seconds = max(1, int(distance / URBAN_AMBULANCE_METERS_PER_SECOND))
        traffic_seconds = int(uncongested_seconds * traffic_level)
        signal_delay = self._signal_penalty_seconds(distance)
        priority_savings = 0
        if use_signal_priority:
            priority_savings = int(signal_delay * PRIORITY_SIGNAL_SAVINGS[priority])

        estimated_duration = max(1, traffic_seconds + signal_delay - priority_savings)
        midpoint = self._midpoint(origin, destination, detour_factor)
        segments = self._build_route_segments(
            origin=origin,
            midpoint=midpoint,
            destination=destination,
            estimated_duration=estimated_duration,
        )
        alternatives: list[BestRouteResponse] = []
        if include_alternatives and variant_name == "fastest":
            alternatives = [
                self._calculate_route_variant(
                    origin,
                    destination,
                    priority,
                    min(2.5, traffic_level * 0.92),
                    use_signal_priority,
                    "traffic-balanced",
                    1.12,
                    False,
                ),
                self._calculate_route_variant(
                    origin,
                    destination,
                    priority,
                    min(2.5, traffic_level * 0.85),
                    use_signal_priority,
                    "signal-light",
                    1.22,
                    False,
                ),
            ]

        return BestRouteResponse(
            estimated_distance_meters=distance,
            estimated_duration_seconds=uncongested_seconds,
            traffic_adjusted_duration_seconds=estimated_duration,
            signal_delay_seconds=signal_delay,
            priority_savings_seconds=priority_savings,
            route_polyline=[origin, midpoint, destination],
            segments=segments,
            alternatives=alternatives,
            rationale=(
                f"Selected {variant_name} healthcare route using ambulance speed profile, "
                "traffic multiplier, intersection delay, and emergency signal priority."
            ),
        )

    def _midpoint(
        self, origin: Coordinate, destination: Coordinate, detour_factor: float
    ) -> Coordinate:
        offset = (detour_factor - 1.0) * 0.015
        return Coordinate(
            latitude=(origin.latitude + destination.latitude) / 2 + offset,
            longitude=(origin.longitude + destination.longitude) / 2 - offset,
        )

    def _build_route_segments(
        self,
        origin: Coordinate,
        midpoint: Coordinate,
        destination: Coordinate,
        estimated_duration: int,
    ) -> list[RouteSegment]:
        first_distance = int(haversine_meters(origin, midpoint))
        second_distance = int(haversine_meters(midpoint, destination))
        first_seconds = max(1, int(estimated_duration * 0.48))
        second_seconds = max(1, estimated_duration - first_seconds)
        return [
            RouteSegment(
                start=origin,
                end=midpoint,
                distance_meters=first_distance,
                estimated_seconds=first_seconds,
                instruction="Proceed on the fastest medically prioritized corridor.",
            ),
            RouteSegment(
                start=midpoint,
                end=destination,
                distance_meters=second_distance,
                estimated_seconds=second_seconds,
                instruction=(
                    "Continue to destination using signal-priority routing where available."
                ),
            ),
        ]
