from datetime import date
from typing import Optional

from django.db.models import Avg, Count
from ninja import Router

from accounts.api import AuthBearer

router = Router()


@router.get("/livestock-summary", auth=AuthBearer())
def livestock_summary_report(
    request, from_date: Optional[date] = None, to_date: Optional[date] = None
):
    """Generate livestock summary report"""
    from livestock.models import Livestock

    queryset = Livestock.objects.filter(owner=request.auth)

    if from_date:
        # Using __date to compare DateTimeField with date
        queryset = queryset.filter(created_at__date__gte=from_date)
    if to_date:
        queryset = queryset.filter(created_at__date__lte=to_date)

    total = queryset.count()
    by_type = queryset.values("animal_type").annotate(count=Count("id"))
    by_status = queryset.values("status").annotate(count=Count("id"))
    avg_weight = queryset.aggregate(avg_weight=Avg("weight"))

    return {
        "report_type": "livestock_summary",
        "period": {"from": from_date, "to": to_date},
        "total_livestock": total,
        "breakdown_by_type": list(by_type),
        "breakdown_by_status": list(by_status),
        "average_weight": avg_weight["avg_weight"],
    }


@router.get("/health-report", auth=AuthBearer())
def health_report(
    request, from_date: Optional[date] = None, to_date: Optional[date] = None
):
    """Generate health report"""
    from health.models import HealthRecord, VaccinationRecord

    health_records = HealthRecord.objects.filter(owner=request.auth)
    vaccinations = VaccinationRecord.objects.filter(owner=request.auth)

    if from_date:
        health_records = health_records.filter(date__gte=from_date)
        vaccinations = vaccinations.filter(scheduled_date__gte=from_date)

    if to_date:
        health_records = health_records.filter(date__lte=to_date)
        vaccinations = vaccinations.filter(scheduled_date__lte=to_date)

    total_records = health_records.count()
    records_by_condition = health_records.values("condition").annotate(
        count=Count("id")
    )

    total_vaccinations = vaccinations.count()
    vaccinations_by_status = vaccinations.values("status").annotate(count=Count("id"))

    return {
        "report_type": "health_report",
        "period": {"from": from_date, "to": to_date},
        "health_records": {
            "total": total_records,
            "by_condition": list(records_by_condition),
        },
        "vaccinations": {
            "total": total_vaccinations,
            "by_status": list(vaccinations_by_status),
        },
    }
