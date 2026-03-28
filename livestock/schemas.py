from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from ninja import Schema


class LivestockSchema(Schema):
    id: UUID
    tag_id: str
    name: Optional[str]
    animal_type: str
    breed: str
    gender: str
    date_of_birth: date
    weight: float
    status: str
    notes: Optional[str]
    created_at: datetime
    age: int  # Computed property


class LivestockCreateSchema(Schema):
    tag_id: str
    name: Optional[str] = ""
    animal_type: str
    breed: str
    gender: str
    date_of_birth: date
    weight: float
    status: str = "healthy"
    notes: Optional[str] = ""


class LivestockUpdateSchema(Schema):
    name: Optional[str] = None
    weight: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class PublicHealthRecordSchema(Schema):
    date: date
    condition: str
    status: str

class PublicVaccinationSchema(Schema):
    vaccine_name: str
    scheduled_date: date
    status: str

class LivestockPublicSchema(Schema):
    tag_id: str
    name: Optional[str]
    animal_type: str
    breed: str
    gender: str
    date_of_birth: date
    weight: float
    status: str
    age: int
    owner_farm: str
    health_records: List[PublicHealthRecordSchema]
    vaccinations: List[PublicVaccinationSchema]
