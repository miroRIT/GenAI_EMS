from uuid import UUID

from emergencypulse.domain.models import (
    Ambulance,
    AmbulanceStatus,
    Coordinate,
    IncidentCreate,
    IncidentSeverity,
    RouteCalculationRequest,
    RoutePriority,
)
from emergencypulse.services.routing import RoutingService, haversine_meters


def test_haversine_distance_is_reasonable_for_manhattan_points() -> None:
    times_square = Coordinate(latitude=40.7580, longitude=-73.9855)
    wall_street = Coordinate(latitude=40.7060, longitude=-74.0086)

    distance = haversine_meters(times_square, wall_street)

    assert 6_000 < distance < 7_000


def test_scoring_prefers_closer_ambulance() -> None:
    service = RoutingService(repository=None)  # type: ignore[arg-type]
    incident = IncidentCreate(
        patient_location=Coordinate(latitude=40.7585, longitude=-73.9860),
        severity=IncidentSeverity.critical,
    )
    near = Ambulance(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        call_sign="MEDIC-01",
        status=AmbulanceStatus.available,
        location=Coordinate(latitude=40.7580, longitude=-73.9855),
        equipment_level=3,
    )
    far = Ambulance(
        id=UUID("22222222-2222-2222-2222-222222222222"),
        call_sign="MEDIC-02",
        status=AmbulanceStatus.available,
        location=Coordinate(latitude=40.7060, longitude=-74.0086),
        equipment_level=5,
    )

    route_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    near_plan = service._score_ambulance(near, incident, route_id)
    far_plan = service._score_ambulance(far, incident, UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))

    assert near_plan.total_score < far_plan.total_score
    assert near_plan.estimated_arrival_seconds < far_plan.estimated_arrival_seconds


def test_best_route_calculation_returns_public_healthcare_route() -> None:
    service = RoutingService()
    request = RouteCalculationRequest(
        origin=Coordinate(latitude=40.7584, longitude=-73.9857),
        destination=Coordinate(latitude=40.7648, longitude=-73.9808),
        priority=RoutePriority.emergency,
        traffic_level=1.35,
    )

    response = service.calculate_best_route(request)

    assert response.estimated_distance_meters > 0
    assert response.traffic_adjusted_duration_seconds > 0
    assert response.priority_savings_seconds > 0
    assert len(response.route_polyline) == 3
    assert len(response.segments) == 2
    assert len(response.alternatives) == 2
