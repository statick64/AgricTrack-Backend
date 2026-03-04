from datetime import date, timedelta
from typing import List, Optional

from ninja import Router

from accounts.api import AuthBearer

from .models import HealthRecord, VaccinationRecord
from .schemas import (
    HealthRecordCreateSchema,
    HealthRecordSchema,
    VaccinationCreateSchema,
    VaccinationSchema,
)

router = Router()


# Health Records
@router.get("/records", response=List[HealthRecordSchema], auth=AuthBearer())
def list_health_records(request):
    """List all health records"""
    return HealthRecord.objects.filter(owner=request.auth)


@router.post("/records", response={201: HealthRecordSchema}, auth=AuthBearer())
def create_health_record(request, data: HealthRecordCreateSchema):
    """Create new health record"""
    record = HealthRecord.objects.create(owner=request.auth, **data.dict())
    return 201, record


# Vaccinations
@router.get("/vaccinations", response=List[VaccinationSchema], auth=AuthBearer())
def list_vaccinations(request, status: Optional[str] = None):
    """List vaccination records"""
    queryset = VaccinationRecord.objects.filter(owner=request.auth)

    if status:
        queryset = queryset.filter(status=status)

    return queryset


@router.post("/vaccinations", response={201: VaccinationSchema}, auth=AuthBearer())
def create_vaccination(request, data: VaccinationCreateSchema):
    """Schedule new vaccination"""
    vaccination = VaccinationRecord.objects.create(owner=request.auth, **data.dict())
    return 201, vaccination


@router.put("/vaccinations/{vax_id}", response=VaccinationSchema, auth=AuthBearer())
def update_vaccination(request, vax_id: int, data: dict):
    """Update vaccination record (e.g., mark as completed)"""
    vaccination = VaccinationRecord.objects.get(id=vax_id, owner=request.auth)

    for key, value in data.items():
        setattr(vaccination, key, value)

    vaccination.save()
    return vaccination


@router.get("/vaccinations/upcoming", auth=AuthBearer())
def get_upcoming_vaccinations(request):
    """Get upcoming vaccinations for dashboard"""
    upcoming = VaccinationRecord.objects.filter(
        owner=request.auth,
        status="pending",
        scheduled_date__lte=date.today() + timedelta(days=7),
    )

    return list(upcoming.values())
