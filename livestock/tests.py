"""
Tests for the Livestock app.
Covers: Livestock model, CRUD APIs, stats, QR code, public profile, owner isolation.
"""

import json
from datetime import date
from decimal import Decimal
from django.test import TestCase, Client
from .models import Livestock
from conftest import create_test_user, create_test_livestock, get_auth_header


class LivestockModelTests(TestCase):
    def setUp(self):
        self.user = create_test_user()

    def test_uuid_pk(self):
        animal = create_test_livestock(self.user)
        self.assertEqual(len(str(animal.id)), 36)

    def test_str_with_name(self):
        animal = create_test_livestock(self.user, name="Bessie")
        self.assertEqual(str(animal), "BW-001 - Bessie")

    def test_str_without_name(self):
        animal = create_test_livestock(self.user, tag_id="BW-002", name="")
        self.assertEqual(str(animal), "BW-002 - cattle")

    def test_age_property(self):
        dob = date(2020, 1, 1)
        animal = create_test_livestock(self.user, tag_id="BW-AGE", date_of_birth=dob)
        expected = date.today().year - 2020
        if date.today().month < 1 or (date.today().month == 1 and date.today().day < 1):
            expected -= 1
        self.assertEqual(animal.age, expected)

    def test_unique_tag_id(self):
        create_test_livestock(self.user, tag_id="BW-UNQ")
        with self.assertRaises(Exception):
            create_test_livestock(self.user, tag_id="BW-UNQ")

    def test_timestamps(self):
        animal = create_test_livestock(self.user, tag_id="BW-TS")
        self.assertIsNotNone(animal.created_at)
        self.assertIsNotNone(animal.updated_at)


class LivestockListAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_test_user()
        self.headers = get_auth_header(self.user)
        create_test_livestock(self.user, tag_id="L-001", animal_type="cattle")
        create_test_livestock(self.user, tag_id="L-002", animal_type="goat")
        create_test_livestock(self.user, tag_id="L-003", animal_type="cattle")

    def test_list_all(self):
        r = self.client.get("/api/livestock/", **self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 3)

    def test_filter_by_type(self):
        r = self.client.get("/api/livestock/", {"animal_type": "cattle"}, **self.headers)
        self.assertEqual(len(r.json()), 2)

    def test_unauthenticated(self):
        r = self.client.get("/api/livestock/")
        self.assertEqual(r.status_code, 401)


class LivestockCRUDAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_test_user()
        self.headers = get_auth_header(self.user)
        self.animal = create_test_livestock(self.user, tag_id="CRUD-001")

    def test_get_single(self):
        r = self.client.get(f"/api/livestock/{self.animal.id}", **self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["tag_id"], "CRUD-001")

    def test_create(self):
        payload = {
            "tag_id": "NEW-001", "name": "Daisy", "animal_type": "cattle",
            "breed": "Brahman", "gender": "female", "date_of_birth": "2022-03-10",
            "weight": 320.5, "status": "healthy", "notes": "New heifer",
        }
        r = self.client.post("/api/livestock/", json.dumps(payload),
                             content_type="application/json", **self.headers)
        self.assertEqual(r.status_code, 201)
        self.assertTrue(Livestock.objects.filter(tag_id="NEW-001").exists())

    def test_update(self):
        payload = {"name": "Updated", "weight": 475.0, "status": "pregnant"}
        r = self.client.put(f"/api/livestock/{self.animal.id}", json.dumps(payload),
                            content_type="application/json", **self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["name"], "Updated")

    def test_delete(self):
        r = self.client.delete(f"/api/livestock/{self.animal.id}", **self.headers)
        self.assertEqual(r.status_code, 204)
        self.assertFalse(Livestock.objects.filter(id=self.animal.id).exists())


class LivestockStatsAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_test_user()
        self.headers = get_auth_header(self.user)
        create_test_livestock(self.user, tag_id="ST-1", animal_type="cattle")
        create_test_livestock(self.user, tag_id="ST-2", animal_type="goat", status="sick")

    def test_stats_summary(self):
        r = self.client.get("/api/livestock/stats/summary", **self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["total"], 2)

    def test_stats_empty(self):
        other = create_test_user(email="empty@example.com")
        r = self.client.get("/api/livestock/stats/summary", **get_auth_header(other))
        self.assertEqual(r.json()["total"], 0)


class LivestockOwnerIsolationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_a = create_test_user(email="a@example.com")
        self.user_b = create_test_user(email="b@example.com")
        self.animal_a = create_test_livestock(self.user_a, tag_id="OWN-A")
        self.animal_b = create_test_livestock(self.user_b, tag_id="OWN-B")

    def test_isolation_list(self):
        r = self.client.get("/api/livestock/", **get_auth_header(self.user_a))
        self.assertEqual(len(r.json()), 1)
        self.assertEqual(r.json()[0]["tag_id"], "OWN-A")

    def test_cannot_access_others(self):
        r = self.client.get(f"/api/livestock/{self.animal_b.id}", **get_auth_header(self.user_a))
        self.assertIn(r.status_code, [403, 404, 500])


class LivestockPublicProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_test_user()
        self.animal = create_test_livestock(self.user, tag_id="PUB-001")

    def test_public_exists(self):
        r = self.client.get("/api/livestock/public/PUB-001")
        self.assertEqual(r.status_code, 200)

    def test_public_not_found(self):
        r = self.client.get("/api/livestock/public/NOPE")
        self.assertEqual(r.status_code, 404)


class LivestockQRCodeAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_test_user()
        self.headers = get_auth_header(self.user)
        self.animal = create_test_livestock(self.user, tag_id="QR-001")

    def test_qrcode_png(self):
        r = self.client.get(f"/api/livestock/{self.animal.id}/qrcode", **self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "image/png")
