from typing import List, Optional

from django.db.models import Count
from ninja import Router

from accounts.api import AuthBearer

from .models import Livestock
from .schemas import LivestockCreateSchema, LivestockSchema, LivestockUpdateSchema

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
def get_livestock(request, livestock_id: int):
    """Get single livestock by ID"""
    return Livestock.objects.get(id=livestock_id, owner=request.auth)


@router.post("/", response={201: LivestockSchema}, auth=AuthBearer())
def create_livestock(request, data: LivestockCreateSchema):
    """Create new livestock"""
    livestock = Livestock.objects.create(owner=request.auth, **data.dict())
    return 201, livestock


@router.put("/{livestock_id}", response=LivestockSchema, auth=AuthBearer())
def update_livestock(request, livestock_id: int, data: LivestockUpdateSchema):
    """Update livestock"""
    livestock = Livestock.objects.get(id=livestock_id, owner=request.auth)

    for attr, value in data.dict(exclude_unset=True).items():
        setattr(livestock, attr, value)

    livestock.save()
    return livestock


@router.delete("/{livestock_id}", response={204: None}, auth=AuthBearer())
def delete_livestock(request, livestock_id: int):
    """Delete livestock"""
    livestock = Livestock.objects.get(id=livestock_id, owner=request.auth)
    livestock.delete()
    return 204, None
