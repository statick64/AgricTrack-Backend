from datetime import datetime
from typing import Optional

from ninja import Schema


class InventoryItemSchema(Schema):
    id: int
    item_name: str
    category: str
    quantity: float
    unit: str
    min_stock_level: float
    status: str
    description: Optional[str]
    supplier: Optional[str]
    cost_per_unit: Optional[float]
    last_updated: datetime
    created_at: datetime


class InventoryItemCreateSchema(Schema):
    item_name: str
    category: str
    quantity: float
    unit: str
    min_stock_level: float
    description: Optional[str] = ""
    supplier: Optional[str] = ""
    cost_per_unit: Optional[float] = None


class InventoryTransactionSchema(Schema):
    id: int
    item_id: int
    transaction_type: str
    quantity: float
    notes: Optional[str]
    transaction_date: datetime


class InventoryTransactionCreateSchema(Schema):
    item_id: int
    transaction_type: str
    quantity: float
    notes: Optional[str] = ""
