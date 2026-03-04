from datetime import datetime, timedelta

import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from ninja import Router
from ninja.security import HttpBearer

from .models import User
from .schemas import ErrorSchema, LoginSchema, RegisterSchema, TokenSchema, UserSchema

router = Router()


class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = User.objects.get(id=payload["user_id"])
            return user
        except:
            return None


@router.post("/register", response={201: TokenSchema, 400: ErrorSchema})
def register(request, data: RegisterSchema):
    """Register a new user"""
    if User.objects.filter(email=data.email).exists():
        return 400, {"error": "Email already registered"}

    full_name_parts = data.full_name.split()
    first_name = full_name_parts[0] if full_name_parts else ""
    last_name = " ".join(full_name_parts[1:]) if len(full_name_parts) > 1 else ""

    user = User.objects.create_user(
        username=data.email,
        email=data.email,
        password=data.password,
        first_name=first_name,
        last_name=last_name,
        farm_name=data.farm_name,
        phone_number=data.phone_number,
        location=data.location,
    )

    # Generate JWT token
    token = jwt.encode(
        {"user_id": user.id, "exp": datetime.utcnow() + timedelta(days=7)},
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    return 201, {"token": token, "user": user}


@router.post("/login", response={200: TokenSchema, 401: ErrorSchema})
def login(request, data: LoginSchema):
    """Login user"""
    user = authenticate(username=data.email, password=data.password)

    if not user:
        return 401, {"error": "Invalid credentials"}

    token = jwt.encode(
        {"user_id": user.id, "exp": datetime.utcnow() + timedelta(days=7)},
        settings.SECRET_KEY,
        algorithm="HS256",
    )

    return {"token": token, "user": user}


@router.get("/me", response=UserSchema, auth=AuthBearer())
def get_current_user(request):
    """Get current authenticated user"""
    return request.auth
