from datetime import datetime
from typing import Optional

from ninja import Schema


class TrainingResourceSchema(Schema):
    id: int
    title: str
    category: str
    description: str
    content: str
    featured_image: Optional[str]
    external_link: Optional[str]
    read_time: int
    is_featured: bool
    published_date: datetime
    updated_at: datetime


class TrainingResourceCreateSchema(Schema):
    title: str
    category: str
    description: str
    content: str
    featured_image: Optional[str] = None
    external_link: Optional[str] = ""
    read_time: int
    is_featured: bool = False
