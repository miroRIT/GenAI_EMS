from sqlalchemy import Select, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from emergencypulse.domain.db_models import AmbulanceRecord, IncidentRecord
from emergencypulse.domain.models import (
    Ambulance,
    AmbulanceStatus,
    Coordinate,
    IncidentCreate,
    RoutePlan,
)


class AmbulanceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_available(self, limit: int = 25) -> list[Ambulance]:
        stmt: Select[tuple[AmbulanceRecord]] = (
            select(AmbulanceRecord)
            .where(AmbulanceRecord.status == AmbulanceStatus.available)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [
            Ambulance(
                id=row.id,
                call_sign=row.call_sign,
                status=row.status,
                location=Coordinate(latitude=row.latitude, longitude=row.longitude),
                equipment_level=row.equipment_level,
            )
            for row in result.scalars().all()
        ]

    async def persist_dispatch(
        self, incident: IncidentCreate, selected_route: RoutePlan
    ) -> IncidentRecord:
        record = IncidentRecord(
            severity=incident.severity,
            patient_latitude=incident.patient_location.latitude,
            patient_longitude=incident.patient_location.longitude,
            destination_latitude=incident.destination.latitude if incident.destination else None,
            destination_longitude=incident.destination.longitude if incident.destination else None,
            notes=incident.notes,
            assigned_ambulance_id=selected_route.ambulance_id,
            eta_seconds=selected_route.estimated_arrival_seconds,
        )
        await self.session.execute(
            update(AmbulanceRecord)
            .where(AmbulanceRecord.id == selected_route.ambulance_id)
            .values(status=AmbulanceStatus.assigned)
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record
