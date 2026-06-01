"""
Tests for the Accounts app.
Covers: User model, registration, login, and authenticated user retrieval.
"""

import json

import jwt
from django.conf import settings
from django.test import TestCase, Client

from .models import User
from conftest import create_test_user, get_auth_header


class UserModelTests(TestCase):
    """Tests for the custom User model."""

    def test_create_user_with_all_fields(self):
        """User can be created with custom fields (farm_name, phone, location)."""
        user = create_test_user()
        self.assertEqual(user.email, "testfarmer@example.com")
        self.assertEqual(user.farm_name, "Test Farm")
        self.assertEqual(user.phone_number, "+26771234567")
        self.assertEqual(user.location, "Gaborone")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")

    def test_str_representation(self):
        """__str__ returns the username."""
        user = create_test_user()
        self.assertEqual(str(user), user.username)

    def test_default_blank_fields(self):
        """Optional fields default to blank strings."""
        user = User.objects.create_user(
            username="minimal@example.com",
            email="minimal@example.com",
            password="pass123",
        )
        self.assertEqual(user.farm_name, "")
        self.assertEqual(user.phone_number, "")
        self.assertEqual(user.location, "")

    def test_created_at_auto_set(self):
        """created_at is automatically populated on creation."""
        user = create_test_user()
        self.assertIsNotNone(user.created_at)


class RegisterAPITests(TestCase):
    """Tests for POST /api/auth/register."""

    def setUp(self):
        self.client = Client()
        self.url = "/api/auth/register"
        self.valid_data = {
            "full_name": "Jane Smith",
            "email": "jane@example.com",
            "password": "securepass123",
            "farm_name": "Smith Ranch",
            "phone_number": "+26777654321",
            "location": "Francistown",
        }

    def test_register_success(self):
        """Successful registration returns 201 with token and user data."""
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], "jane@example.com")
        self.assertEqual(data["user"]["first_name"], "Jane")
        self.assertEqual(data["user"]["last_name"], "Smith")

    def test_register_splits_full_name(self):
        """Full name is correctly split into first_name and last_name."""
        self.valid_data["full_name"] = "Mary Ann Johnson"
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_data),
            content_type="application/json",
        )
        data = response.json()
        self.assertEqual(data["user"]["first_name"], "Mary")
        self.assertEqual(data["user"]["last_name"], "Ann Johnson")

    def test_register_single_name(self):
        """A single-word name uses it as first_name, last_name is blank."""
        self.valid_data["full_name"] = "Thabo"
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_data),
            content_type="application/json",
        )
        data = response.json()
        self.assertEqual(data["user"]["first_name"], "Thabo")
        self.assertEqual(data["user"]["last_name"], "")

    def test_register_duplicate_email(self):
        """Registering with an existing email returns 400."""
        create_test_user(email="jane@example.com")
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Email already registered")

    def test_register_returns_valid_jwt(self):
        """The returned token is a valid JWT containing the user_id."""
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_data),
            content_type="application/json",
        )
        token = response.json()["token"]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        self.assertIn("user_id", payload)
        self.assertIn("exp", payload)


class LoginAPITests(TestCase):
    """Tests for POST /api/auth/login."""

    def setUp(self):
        self.client = Client()
        self.url = "/api/auth/login"
        self.user = create_test_user(email="login@example.com", password="mypassword")

    def test_login_success(self):
        """Valid credentials return 200 with token and user."""
        response = self.client.post(
            self.url,
            data=json.dumps({"email": "login@example.com", "password": "mypassword"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], "login@example.com")

    def test_login_wrong_password(self):
        """Wrong password returns 401."""
        response = self.client.post(
            self.url,
            data=json.dumps({"email": "login@example.com", "password": "wrongpass"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "Invalid credentials")

    def test_login_nonexistent_user(self):
        """Non-existent email returns 401."""
        response = self.client.post(
            self.url,
            data=json.dumps({"email": "nobody@example.com", "password": "pass123"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)


class GetCurrentUserAPITests(TestCase):
    """Tests for GET /api/auth/me."""

    def setUp(self):
        self.client = Client()
        self.url = "/api/auth/me"
        self.user = create_test_user()

    def test_get_me_authenticated(self):
        """Authenticated request returns the current user's data."""
        response = self.client.get(self.url, **get_auth_header(self.user))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], self.user.email)
        self.assertEqual(data["farm_name"], self.user.farm_name)

    def test_get_me_unauthenticated(self):
        """Request without token returns 401."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_get_me_invalid_token(self):
        """Request with an invalid token returns 401."""
        response = self.client.get(
            self.url, HTTP_AUTHORIZATION="Bearer invalid.token.here"
        )
        self.assertEqual(response.status_code, 401)
