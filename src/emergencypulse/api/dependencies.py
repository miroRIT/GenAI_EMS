from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from emergencypulse.db.session import get_session
from emergencypulse.repositories.ambulance_repository import AmbulanceRepository
from emergencypulse.services.routing import RoutingService


def get_ambulance_repository(
    session: AsyncSession = Depends(get_session),
) -> AmbulanceRepository:
    return AmbulanceRepository(session)


def get_routing_service(
    repository: AmbulanceRepository = Depends(get_ambulance_repository),
) -> RoutingService:
    return RoutingService(repository)


def get_public_routing_service() -> RoutingService:
    return RoutingService()
