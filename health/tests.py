"""
Tests for the Health app.
Covers: HealthRecord/VaccinationRecord models, CRUD APIs, upcoming vaccinations, owner isolation.
"""

import json
from datetime import date, timedelta
from django.test import TestCase, Client
from .models import HealthRecord, VaccinationRecord
from conftest import (
    create_test_user, create_test_livestock, get_auth_header,
    create_test_health_record, create_test_vaccination,
)


class HealthRecordModelTests(TestCase):
    def setUp(self):
        self.user = create_test_user()
        self.animal = create_test_livestock(self.user)

    def test_create_record(self):
        rec = create_test_health_record(self.user, self.animal)
        self.assertEqual(rec.condition, "Foot rot")
        self.assertEqual(rec.owner, self.user)
        self.assertEqual(rec.animal, self.animal)

    def test_str_representation(self):
        rec = create_test_health_record(self.user, self.animal, date=date(2025, 6, 1))
        self.assertIn(self.animal.tag_id, str(rec))
        self.assertIn("Foot rot", str(rec))

    def test_timestamps(self):
        rec = create_test_health_record(self.user, self.animal)
        self.assertIsNotNone(rec.created_at)
        self.assertIsNotNone(rec.updated_at)


class VaccinationModelTests(TestCase):
    def setUp(self):
        self.user = create_test_user()
        self.animal = create_test_livestock(self.user)

    def test_create_individual_vaccination(self):
        vax = create_test_vaccination(self.user, self.animal)
        self.assertEqual(vax.vaccine_name, "FMD Vaccine")
        self.assertEqual(vax.animal, self.animal)

    def test_create_group_vaccination(self):
        vax = create_test_vaccination(
            self.user, animal=None, group_name="Herd A",
            vaccine_name="Anthrax Vaccine",
        )
        self.assertIsNone(vax.animal)
        self.assertEqual(vax.group_name, "Herd A")

    def test_str_individual(self):
        vax = create_test_vaccination(self.user, self.animal)
        self.assertIn(self.animal.tag_id, str(vax))

    def test_str_group(self):
        vax = create_test_vaccination(self.user, animal=None, group_name="Herd B")
        self.assertIn("Herd B", str(vax))

    def test_default_status_pending(self):
        vax = create_test_vaccination(self.user, self.animal)
        self.assertEqual(vax.status, "pending")


class HealthRecordAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_test_user()
        self.headers = get_auth_header(self.user)
        self.animal = create_test_livestock(self.user)
        self.record = create_test_health_record(self.user, self.animal)

    def test_list_records(self):
        r = self.client.get("/api/health/records", **self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 1)

    def test_create_record(self):
        payload = {
            "animal_id": str(self.animal.id),
            "date": str(date.today()),
            "condition": "Bloating",
            "treatment": "Trocar procedure",
            "veterinarian": "Dr. Kgosi",
            "status": "ongoing",
            "notes": "Monitor closely",
        }
        r = self.client.post("/api/health/records", json.dumps(payload),
                             content_type="application/json", **self.headers)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["condition"], "Bloating")

    def test_unauthenticated(self):
        r = self.client.get("/api/health/records")
        self.assertEqual(r.status_code, 401)


class VaccinationAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_test_user()
        self.headers = get_auth_header(self.user)
        self.animal = create_test_livestock(self.user)
        self.vax = create_test_vaccination(self.user, self.animal)

    def test_list_vaccinations(self):
        r = self.client.get("/api/health/vaccinations", **self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 1)

    def test_filter_by_status(self):
        create_test_vaccination(
            self.user, self.animal, vaccine_name="Completed Vax",
            status="completed", scheduled_date=date.today(),
        )
        r = self.client.get("/api/health/vaccinations", {"status": "pending"}, **self.headers)
        data = r.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["status"], "pending")

    def test_create_vaccination(self):
        payload = {
            "animal_id": str(self.animal.id),
            "vaccine_name": "Brucella Vaccine",
            "scheduled_date": str(date.today() + timedelta(days=5)),
            "status": "pending",
        }
        r = self.client.post("/api/health/vaccinations", json.dumps(payload),
                             content_type="application/json", **self.headers)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["vaccine_name"], "Brucella Vaccine")

    def test_update_vaccination(self):
        payload = {"status": "completed", "administered_date": str(date.today())}
        r = self.client.put(f"/api/health/vaccinations/{self.vax.id}",
                            json.dumps(payload), content_type="application/json",
                            **self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "completed")


class UpcomingVaccinationsAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_test_user()
        self.headers = get_auth_header(self.user)
        self.animal = create_test_livestock(self.user)
        # Within 7 days
        create_test_vaccination(
            self.user, self.animal, vaccine_name="Soon Vax",
            scheduled_date=date.today() + timedelta(days=3), status="pending",
        )
        # Beyond 7 days
        create_test_vaccination(
            self.user, self.animal, vaccine_name="Later Vax",
            scheduled_date=date.today() + timedelta(days=30), status="pending",
        )

    def test_upcoming_within_7_days(self):
        r = self.client.get("/api/health/vaccinations/upcoming", **self.headers)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["vaccine_name"], "Soon Vax")


class HealthOwnerIsolationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_a = create_test_user(email="ha@example.com")
        self.user_b = create_test_user(email="hb@example.com")
        animal_a = create_test_livestock(self.user_a, tag_id="HA-1")
        animal_b = create_test_livestock(self.user_b, tag_id="HB-1")
        create_test_health_record(self.user_a, animal_a)
        create_test_health_record(self.user_b, animal_b, condition="Mastitis")

    def test_records_isolated(self):
        r = self.client.get("/api/health/records", **get_auth_header(self.user_a))
        data = r.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["condition"], "Foot rot")
