from typing import List, Optional

from ninja import Router

from accounts.api import AuthBearer

from .models import TrainingResource
from .schemas import TrainingResourceCreateSchema, TrainingResourceSchema

router = Router()


@router.get("/", response=List[TrainingResourceSchema], auth=AuthBearer())
def list_resources(request, category: Optional[str] = None):
    """List all training resources"""
    queryset = TrainingResource.objects.all()

    if category:
        queryset = queryset.filter(category=category)

    return queryset


@router.get("/featured", response=List[TrainingResourceSchema], auth=AuthBearer())
def get_featured_resources(request):
    """Get featured training resources"""
    return TrainingResource.objects.filter(is_featured=True)


@router.get("/{resource_id}", response=TrainingResourceSchema, auth=AuthBearer())
def get_resource(request, resource_id: int):
    """Get single training resource"""
    return TrainingResource.objects.get(id=resource_id)


@router.post("/", response={201: TrainingResourceSchema}, auth=AuthBearer())
def create_resource(request, data: TrainingResourceCreateSchema):
    """Create new training resource"""
    resource = TrainingResource.objects.create(**data.dict())
    return 201, resource


@router.put("/{resource_id}", response=TrainingResourceSchema, auth=AuthBearer())
def update_resource(request, resource_id: int, data: dict):
    """Update training resource"""
    resource = TrainingResource.objects.get(id=resource_id)

    for key, value in data.items():
        setattr(resource, key, value)

    resource.save()
    return resource


@router.delete("/{resource_id}", response={204: None}, auth=AuthBearer())
def delete_resource(request, resource_id: int):
    """Delete training resource"""
    resource = TrainingResource.objects.get(id=resource_id)
    resource.delete()
    return 204, None
