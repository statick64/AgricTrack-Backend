from datetime import date, datetime
from typing import Optional

from ninja import Schema


class HealthRecordSchema(Schema):
    id: int
    animal_id: int
    date: date
    condition: str
    treatment: str
    veterinarian: str
    status: str
    notes: Optional[str]
    follow_up_date: Optional[date]
    created_at: datetime
    updated_at: datetime


class HealthRecordCreateSchema(Schema):
    animal_id: int
    date: date
    condition: str
    treatment: str
    veterinarian: str
    status: str
    notes: Optional[str] = ""
    follow_up_date: Optional[date] = None


class VaccinationSchema(Schema):
    id: int
    animal_id: Optional[int]
    group_name: Optional[str]
    vaccine_name: str
    scheduled_date: date
    administered_date: Optional[date]
    administered_by: Optional[str]
    status: str
    batch_number: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class VaccinationCreateSchema(Schema):
    animal_id: Optional[int] = None
    group_name: Optional[str] = ""
    vaccine_name: str
    scheduled_date: date
    administered_date: Optional[date] = None
    administered_by: Optional[str] = ""
    status: str = "pending"
    batch_number: Optional[str] = ""
    notes: Optional[str] = ""
