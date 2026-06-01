"""
Shared test helpers for the AgricTrack backend test suite.
Provides utility functions for creating test users, generating JWT tokens,
and building common test data used across multiple app test modules.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

import jwt
from django.conf import settings

from accounts.models import User


def create_test_user(
    email="testfarmer@example.com",
    password="testpass123",
    full_name="John Doe",
    farm_name="Test Farm",
    phone_number="+26771234567",
    location="Gaborone",
):
    """Create and return a test user with known credentials."""
    name_parts = full_name.split()
    first_name = name_parts[0] if name_parts else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        farm_name=farm_name,
        phone_number=phone_number,
        location=location,
    )
    return user


def get_auth_token(user):
    """Generate a valid JWT token for the given user."""
    token = jwt.encode(
        {"user_id": user.id, "exp": datetime.utcnow() + timedelta(days=7)},
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    return token


def get_auth_header(user):
    """Return an Authorization header dict for authenticated requests."""
    token = get_auth_token(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def create_test_livestock(owner, **overrides):
    """Create and return a test Livestock instance."""
    from livestock.models import Livestock

    defaults = {
        "owner": owner,
        "tag_id": "BW-001",
        "name": "Bessie",
        "animal_type": "cattle",
        "breed": "Tswana",
        "gender": "female",
        "date_of_birth": date(2020, 6, 15),
        "weight": Decimal("450.50"),
        "status": "healthy",
        "notes": "Test animal",
    }
    defaults.update(overrides)
    return Livestock.objects.create(**defaults)


def create_test_health_record(owner, animal, **overrides):
    """Create and return a test HealthRecord instance."""
    from health.models import HealthRecord

    defaults = {
        "animal": animal,
        "owner": owner,
        "date": date.today(),
        "condition": "Foot rot",
        "treatment": "Antibiotics course",
        "veterinarian": "Dr. Moeng",
        "status": "ongoing",
        "notes": "Check in 3 days",
    }
    defaults.update(overrides)
    return HealthRecord.objects.create(**defaults)


def create_test_vaccination(owner, animal=None, **overrides):
    """Create and return a test VaccinationRecord instance."""
    from health.models import VaccinationRecord

    defaults = {
        "animal": animal,
        "owner": owner,
        "vaccine_name": "FMD Vaccine",
        "scheduled_date": date.today() + timedelta(days=3),
        "status": "pending",
    }
    defaults.update(overrides)
    return VaccinationRecord.objects.create(**defaults)


def create_test_inventory_item(owner, **overrides):
    """Create and return a test InventoryItem instance."""
    from inventory.models import InventoryItem

    defaults = {
        "owner": owner,
        "item_name": "Cattle Feed Premium",
        "category": "feed",
        "quantity": Decimal("100.00"),
        "unit": "Bags",
        "min_stock_level": Decimal("10.00"),
        "description": "High protein cattle feed",
        "supplier": "FeedCo Botswana",
        "cost_per_unit": Decimal("250.00"),
    }
    defaults.update(overrides)
    return InventoryItem.objects.create(**defaults)


def create_test_training_resource(**overrides):
    """Create and return a test TrainingResource instance."""
    from training.models import TrainingResource

    defaults = {
        "title": "Cattle Health Management 101",
        "category": "animal_health",
        "description": "A guide to keeping cattle healthy.",
        "content": "Full article content goes here...",
        "read_time": 5,
        "is_featured": False,
    }
    defaults.update(overrides)
    return TrainingResource.objects.create(**defaults)
