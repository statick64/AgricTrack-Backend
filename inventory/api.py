from typing import List, Optional

from ninja import Router

from accounts.api import AuthBearer

from .models import InventoryItem, InventoryTransaction
from .schemas import (
    InventoryItemCreateSchema,
    InventoryItemSchema,
    InventoryTransactionCreateSchema,
    InventoryTransactionSchema,
)

router = Router()


@router.get("/items", response=List[InventoryItemSchema], auth=AuthBearer())
def list_items(request, category: Optional[str] = None):
    """List all inventory items"""
    queryset = InventoryItem.objects.filter(owner=request.auth)

    if category:
        queryset = queryset.filter(category=category)

    return queryset


@router.get("/items/{item_id}", response=InventoryItemSchema, auth=AuthBearer())
def get_item(request, item_id: int):
    """Get single inventory item"""
    return InventoryItem.objects.get(id=item_id, owner=request.auth)


@router.post("/items", response={201: InventoryItemSchema}, auth=AuthBearer())
def create_item(request, data: InventoryItemCreateSchema):
    """Create new inventory item"""
    item = InventoryItem.objects.create(owner=request.auth, **data.dict())
    return 201, item


@router.put("/items/{item_id}", response=InventoryItemSchema, auth=AuthBearer())
def update_item(request, item_id: int, data: dict):
    """Update inventory item"""
    item = InventoryItem.objects.get(id=item_id, owner=request.auth)

    for key, value in data.items():
        setattr(item, key, value)

    item.save()
    return item


@router.delete("/items/{item_id}", response={204: None}, auth=AuthBearer())
def delete_item(request, item_id: int):
    """Delete inventory item"""
    item = InventoryItem.objects.get(id=item_id, owner=request.auth)
    item.delete()
    return 204, None


@router.get(
    "/transactions", response=List[InventoryTransactionSchema], auth=AuthBearer()
)
def list_transactions(request):
    """List inventory transactions"""
    return InventoryTransaction.objects.filter(item__owner=request.auth)


@router.post(
    "/transactions", response={201: InventoryTransactionSchema}, auth=AuthBearer()
)
def create_transaction(request, data: InventoryTransactionCreateSchema):
    """Record a transaction and update inventory quantity"""
    item = InventoryItem.objects.get(id=data.item_id, owner=request.auth)

    # Create transaction
    transaction = InventoryTransaction.objects.create(
        item=item,
        transaction_type=data.transaction_type,
        quantity=data.quantity,
        notes=data.notes,
    )

    # Update item quantity
    if data.transaction_type == "add":
        item.quantity += data.quantity
    elif data.transaction_type == "use":
        item.quantity -= data.quantity
    # For 'adjust', we might need more specific logic, but often it's used for corrections
    # We'll leave it as manual update or handled via simple add/subtract logic if needed later

    item.save()

    return 201, transaction
