from fastapi import APIRouter, Body, Depends, status

from emergencypulse.api.dependencies import get_routing_service
from emergencypulse.core.security import require_scope
from emergencypulse.domain.models import DispatchDecision, IncidentCreate
from emergencypulse.services.routing import RoutingService

router = APIRouter(prefix="/dispatch", tags=["dispatch"])


@router.post(
    "/incidents",
    response_model=DispatchDecision,
    status_code=status.HTTP_201_CREATED,
    summary="Dispatch the best ambulance for an incident",
    description=(
        "Scores available ambulances by estimated arrival time, traffic proxy, signal timing "
        "penalty, incident severity, and equipment capability, then persists the assignment."
    ),
    dependencies=[Depends(require_scope("dispatch:write"))],
    responses={
        201: {"description": "Incident dispatched and ranked alternatives returned."},
        401: {"description": "Missing or invalid bearer token."},
        403: {"description": "Bearer token does not include dispatch:write scope."},
        409: {"description": "No available ambulances are online."},
        422: {"description": "Request validation failed."},
    },
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "criticalCardiacIncident": {
                            "summary": "Critical cardiac incident",
                            "description": (
                                "Dispatch an ALS-capable ambulance near Midtown Manhattan."
                            ),
                            "value": {
                                "patient_location": {
                                    "latitude": 40.7584,
                                    "longitude": -73.9857,
                                },
                                "destination": {"latitude": 40.7648, "longitude": -73.9808},
                                "severity": "critical",
                                "notes": "Chest pain with shortness of breath",
                            },
                        },
                        "lowSeverityTransport": {
                            "summary": "Low severity transport",
                            "description": (
                                "Dispatch a basic life support unit for a stable patient."
                            ),
                            "value": {
                                "patient_location": {
                                    "latitude": 40.7306,
                                    "longitude": -73.9352,
                                },
                                "severity": "low",
                                "notes": "Stable patient transfer request",
                            },
                        },
                    }
                }
            }
        }
    },
)
async def dispatch_incident(
    incident: IncidentCreate = Body(...),
    routing_service: RoutingService = Depends(get_routing_service),
) -> DispatchDecision:
    return await routing_service.dispatch(incident)
