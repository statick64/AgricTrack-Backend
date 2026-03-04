from datetime import datetime
from typing import Optional

from ninja import Schema


class RegisterSchema(Schema):
    full_name: str
    email: str
    password: str
    farm_name: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None


class LoginSchema(Schema):
    email: str
    password: str


class UserSchema(Schema):
    id: int
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    farm_name: Optional[str]
    phone_number: Optional[str]
    location: Optional[str]
    profile_picture: Optional[str] = None
    created_at: datetime


class TokenSchema(Schema):
    token: str
    user: UserSchema


class ErrorSchema(Schema):
    error: str
