from typing import List, Optional
from uuid import UUID

import qrcode
from django.conf import settings
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from ninja import Router

from accounts.api import AuthBearer

from .models import Livestock
from .schemas import (
    LivestockCreateSchema,
    LivestockPublicSchema,
    LivestockSchema,
    LivestockUpdateSchema,
)

router = Router()


@router.get("/stats/summary", auth=AuthBearer())
def get_livestock_stats(request):
    """Get livestock statistics for dashboard"""
    total = Livestock.objects.filter(owner=request.auth).count()
    by_type = (
        Livestock.objects.filter(owner=request.auth)
        .values("animal_type")
        .annotate(count=Count("id"))
    )
    by_status = (
        Livestock.objects.filter(owner=request.auth)
        .values("status")
        .annotate(count=Count("id"))
    )

    return {
        "total": total,
        "by_type": list(by_type),
        "by_status": list(by_status),
    }


@router.get("/", response=List[LivestockSchema], auth=AuthBearer())
def list_livestock(request, animal_type: Optional[str] = None):
    """List all livestock for authenticated user"""
    queryset = Livestock.objects.filter(owner=request.auth)

    if animal_type:
        queryset = queryset.filter(animal_type=animal_type)

    return queryset


@router.get("/{livestock_id}", response=LivestockSchema, auth=AuthBearer())
def get_livestock(request, livestock_id: UUID):
    """Get single livestock by ID"""
    return Livestock.objects.get(id=livestock_id, owner=request.auth)


@router.post("/", response={201: LivestockSchema}, auth=AuthBearer())
def create_livestock(request, data: LivestockCreateSchema):
    """Create new livestock"""
    livestock = Livestock.objects.create(owner=request.auth, **data.dict())
    return 201, livestock


@router.put("/{livestock_id}", response=LivestockSchema, auth=AuthBearer())
def update_livestock(request, livestock_id: UUID, data: LivestockUpdateSchema):
    """Update livestock"""
    livestock = Livestock.objects.get(id=livestock_id, owner=request.auth)

    for attr, value in data.dict(exclude_unset=True).items():
        setattr(livestock, attr, value)

    livestock.save()
    return livestock


@router.delete("/{livestock_id}", response={204: None}, auth=AuthBearer())
def delete_livestock(request, livestock_id: UUID):
    """Delete livestock"""
    livestock = Livestock.objects.get(id=livestock_id, owner=request.auth)
    livestock.delete()
    return 204, None


@router.get("/{livestock_id}/qrcode", auth=AuthBearer())
def generate_qrcode(request, livestock_id: UUID):
    """Generate a QR code for a livestock animal"""
    livestock = get_object_or_404(Livestock, id=livestock_id, owner=request.auth)

    # Generate the public URL
    base_url = getattr(settings, "QR_CODE_BASE_URL", "http://localhost:8000").rstrip("/")
    public_url = f"{base_url}/api/livestock/public/{livestock.tag_id}"

    # Create QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(public_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Return as image response
    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")
    return response


@router.get("/public/{tag_id}")
def get_public_livestock(request, tag_id: str):
    """Get public details of a livestock animal via QR code scan"""
    livestock = get_object_or_404(Livestock, tag_id=tag_id)

    # Prepare nested data
    health_records = [
        {
            "date": hr.date,
            "condition": hr.condition,
            "status": hr.status,
        }
        for hr in livestock.health_records.order_by("-date")[:5]
    ]

    vaccinations = [
        {
            "vaccine_name": v.vaccine_name,
            "scheduled_date": v.scheduled_date,
            "status": v.status,
        }
        for v in livestock.vaccinations.order_by("-scheduled_date")[:5]
    ]

    # Owner farm name
    owner_farm = livestock.owner.farm_name if livestock.owner and livestock.owner.farm_name else "Unknown Farm"

    context = {
        "tag_id": livestock.tag_id,
        "name": livestock.name,
        "animal_type": livestock.animal_type,
        "breed": livestock.breed,
        "gender": livestock.gender,
        "date_of_birth": livestock.date_of_birth,
        "weight": livestock.weight,
        "status": livestock.status,
        "age": livestock.age,
        "owner_farm": owner_farm,
        "health_records": health_records,
        "vaccinations": vaccinations,
    }
    return render(request, "livestock/public_profile.html", context)
