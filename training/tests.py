"""
Tests for the Training app.
Covers: TrainingResource model, CRUD APIs, featured resources, category filtering.
"""

import json
from django.test import TestCase, Client
from .models import TrainingResource
from conftest import create_test_user, create_test_training_resource, get_auth_header


class TrainingResourceModelTests(TestCase):
    def test_create_resource(self):
        res = create_test_training_resource()
        self.assertEqual(res.title, "Cattle Health Management 101")
        self.assertEqual(res.category, "animal_health")
        self.assertIsNotNone(res.published_date)

    def test_str_representation(self):
        res = create_test_training_resource(title="My Article")
        self.assertEqual(str(res), "My Article")

    def test_default_not_featured(self):
        res = create_test_training_resource()
        self.assertFalse(res.is_featured)

    def test_timestamps(self):
        res = create_test_training_resource()
        self.assertIsNotNone(res.published_date)
        self.assertIsNotNone(res.updated_at)


class TrainingListAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_test_user()
        self.headers = get_auth_header(self.user)
        create_test_training_resource(title="Health Guide", category="animal_health")
        create_test_training_resource(title="Farm Tips", category="farm_management")
        create_test_training_resource(title="Nutrition 101", category="nutrition")

    def test_list_all(self):
        r = self.client.get("/api/training/", **self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 3)

    def test_filter_by_category(self):
        r = self.client.get("/api/training/", {"category": "animal_health"}, **self.headers)
        data = r.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["category"], "animal_health")

    def test_unauthenticated(self):
        r = self.client.get("/api/training/")
        self.assertEqual(r.status_code, 401)


class TrainingFeaturedAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_test_user()
        self.headers = get_auth_header(self.user)
        create_test_training_resource(title="Featured One", is_featured=True)
        create_test_training_resource(title="Featured Two", is_featured=True)
        create_test_training_resource(title="Not Featured", is_featured=False)

    def test_featured_only(self):
        r = self.client.get("/api/training/featured", **self.headers)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(len(data), 2)
        for item in data:
            self.assertTrue(item["is_featured"])


class TrainingCRUDAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_test_user()
        self.headers = get_auth_header(self.user)
        self.resource = create_test_training_resource()

    def test_get_single(self):
        r = self.client.get(f"/api/training/{self.resource.id}", **self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["title"], "Cattle Health Management 101")

    def test_create(self):
        payload = {
            "title": "New Guide", "category": "farm_management",
            "description": "Desc", "content": "Content here",
            "read_time": 10, "is_featured": False,
        }
        r = self.client.post("/api/training/", json.dumps(payload),
                             content_type="application/json", **self.headers)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["title"], "New Guide")
        self.assertTrue(TrainingResource.objects.filter(title="New Guide").exists())

    def test_update(self):
        payload = {"title": "Updated Title"}
        r = self.client.put(f"/api/training/{self.resource.id}", json.dumps(payload),
                            content_type="application/json", **self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["title"], "Updated Title")

    def test_delete(self):
        r = self.client.delete(f"/api/training/{self.resource.id}", **self.headers)
        self.assertEqual(r.status_code, 204)
        self.assertFalse(TrainingResource.objects.filter(id=self.resource.id).exists())
