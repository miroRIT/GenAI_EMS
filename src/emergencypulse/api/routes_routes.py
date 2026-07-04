from fastapi import APIRouter, Body, Depends, status

from emergencypulse.api.dependencies import get_public_routing_service
from emergencypulse.domain.models import BestRouteResponse, RouteCalculationRequest
from emergencypulse.services.routing import RoutingService

router = APIRouter(prefix="/routes", tags=["routes"])


@router.post(
    "/best",
    response_model=BestRouteResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate the best open healthcare route",
    description=(
        "Calculates an optimized ambulance or healthcare-service route from origin to "
        "destination using distance, traffic level, intersection delay, and optional "
        "emergency signal-priority savings. This endpoint is intentionally public so "
        "healthcare integrations can validate route estimates without creating a dispatch."
    ),
    responses={
        200: {"description": "Best route calculation returned."},
        422: {"description": "Request validation failed."},
    },
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "emergencyAmbulanceRoute": {
                            "summary": "Emergency ambulance route",
                            "description": "Calculate an emergency route to a trauma center.",
                            "value": {
                                "origin": {"latitude": 40.7584, "longitude": -73.9857},
                                "destination": {"latitude": 40.7648, "longitude": -73.9808},
                                "priority": "emergency",
                                "include_alternatives": True,
                                "use_signal_priority": True,
                                "traffic_level": 1.35,
                            },
                        },
                        "routineHealthcareTransfer": {
                            "summary": "Routine healthcare transfer",
                            "description": "Estimate route timing without emergency preemption.",
                            "value": {
                                "origin": {"latitude": 40.7306, "longitude": -73.9352},
                                "destination": {"latitude": 40.7060, "longitude": -74.0086},
                                "priority": "routine",
                                "include_alternatives": False,
                                "use_signal_priority": False,
                                "traffic_level": 1.1,
                            },
                        },
                    }
                }
            }
        }
    },
)
async def calculate_best_route(
    request: RouteCalculationRequest = Body(...),
    routing_service: RoutingService = Depends(get_public_routing_service),
) -> BestRouteResponse:
    return routing_service.calculate_best_route(request)
