"""
Tests for the Inventory app.
Covers: InventoryItem auto-status, InventoryTransaction, CRUD APIs, transactions, owner isolation.
"""

import json
from decimal import Decimal
from django.test import TestCase, Client
from .models import InventoryItem, InventoryTransaction
from conftest import create_test_user, create_test_inventory_item, get_auth_header


class InventoryItemModelTests(TestCase):
    def setUp(self):
        self.user = create_test_user()

    def test_auto_status_in_stock(self):
        item = create_test_inventory_item(self.user, quantity=Decimal("100"), min_stock_level=Decimal("10"))
        self.assertEqual(item.status, "in_stock")

    def test_auto_status_low_stock(self):
        item = create_test_inventory_item(self.user, item_name="Low Feed",
                                          quantity=Decimal("5"), min_stock_level=Decimal("10"))
        self.assertEqual(item.status, "low_stock")

    def test_auto_status_out_of_stock(self):
        item = create_test_inventory_item(self.user, item_name="Empty Feed",
                                          quantity=Decimal("0"), min_stock_level=Decimal("10"))
        self.assertEqual(item.status, "out_of_stock")

    def test_auto_status_at_min_level(self):
        """Quantity equal to min_stock_level should be low_stock."""
        item = create_test_inventory_item(self.user, item_name="Edge Feed",
                                          quantity=Decimal("10"), min_stock_level=Decimal("10"))
        self.assertEqual(item.status, "low_stock")

    def test_str_representation(self):
        item = create_test_inventory_item(self.user)
        self.assertIn("Cattle Feed Premium", str(item))
        self.assertIn("Bags", str(item))

    def test_timestamps(self):
        item = create_test_inventory_item(self.user)
        self.assertIsNotNone(item.created_at)
        self.assertIsNotNone(item.last_updated)


class InventoryTransactionModelTests(TestCase):
    def setUp(self):
        self.user = create_test_user()
        self.item = create_test_inventory_item(self.user)

    def test_create_transaction(self):
        txn = InventoryTransaction.objects.create(
            item=self.item, transaction_type="add", quantity=Decimal("50"), notes="Restock",
        )
        self.assertEqual(txn.transaction_type, "add")
        self.assertIsNotNone(txn.transaction_date)

    def test_str_representation(self):
        txn = InventoryTransaction.objects.create(
            item=self.item, transaction_type="use", quantity=Decimal("10"),
        )
        self.assertIn("use", str(txn))
        self.assertIn("Cattle Feed Premium", str(txn))


class InventoryItemAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_test_user()
        self.headers = get_auth_header(self.user)
        self.item = create_test_inventory_item(self.user)

    def test_list_items(self):
        r = self.client.get("/api/inventory/items", **self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 1)

    def test_filter_by_category(self):
        create_test_inventory_item(self.user, item_name="Syringe", category="equipment")
        r = self.client.get("/api/inventory/items", {"category": "feed"}, **self.headers)
        self.assertEqual(len(r.json()), 1)
        self.assertEqual(r.json()[0]["category"], "feed")

    def test_get_single_item(self):
        r = self.client.get(f"/api/inventory/items/{self.item.id}", **self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["item_name"], "Cattle Feed Premium")

    def test_create_item(self):
        payload = {
            "item_name": "Antibiotics", "category": "medicine",
            "quantity": 25, "unit": "Bottles", "min_stock_level": 5,
            "description": "Broad-spectrum", "supplier": "VetSupply",
        }
        r = self.client.post("/api/inventory/items", json.dumps(payload),
                             content_type="application/json", **self.headers)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["item_name"], "Antibiotics")

    def test_update_item(self):
        payload = {"quantity": 200}
        r = self.client.put(f"/api/inventory/items/{self.item.id}", json.dumps(payload),
                            content_type="application/json", **self.headers)
        self.assertEqual(r.status_code, 200)

    def test_delete_item(self):
        r = self.client.delete(f"/api/inventory/items/{self.item.id}", **self.headers)
        self.assertEqual(r.status_code, 204)
        self.assertFalse(InventoryItem.objects.filter(id=self.item.id).exists())

    def test_unauthenticated(self):
        r = self.client.get("/api/inventory/items")
        self.assertEqual(r.status_code, 401)


class InventoryTransactionAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_test_user()
        self.headers = get_auth_header(self.user)
        self.item = create_test_inventory_item(self.user, quantity=Decimal("100"))

    def test_list_transactions(self):
        InventoryTransaction.objects.create(
            item=self.item, transaction_type="add", quantity=Decimal("10"),
        )
        r = self.client.get("/api/inventory/transactions", **self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 1)

    def test_create_add_transaction(self):
        payload = {
            "item_id": self.item.id, "transaction_type": "add",
            "quantity": 50, "notes": "New delivery",
        }
        r = self.client.post("/api/inventory/transactions", json.dumps(payload),
                             content_type="application/json", **self.headers)
        self.assertEqual(r.status_code, 201)
        # Verify quantity updated
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, Decimal("150"))

    def test_create_use_transaction(self):
        payload = {
            "item_id": self.item.id, "transaction_type": "use",
            "quantity": 30, "notes": "Daily feeding",
        }
        r = self.client.post("/api/inventory/transactions", json.dumps(payload),
                             content_type="application/json", **self.headers)
        self.assertEqual(r.status_code, 201)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, Decimal("70"))

    def test_use_triggers_low_stock(self):
        """Using enough quantity triggers low_stock status."""
        payload = {
            "item_id": self.item.id, "transaction_type": "use",
            "quantity": 95, "notes": "Big feeding",
        }
        self.client.post("/api/inventory/transactions", json.dumps(payload),
                         content_type="application/json", **self.headers)
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, "low_stock")


class InventoryOwnerIsolationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_a = create_test_user(email="ia@example.com")
        self.user_b = create_test_user(email="ib@example.com")
        create_test_inventory_item(self.user_a, item_name="Feed A")
        create_test_inventory_item(self.user_b, item_name="Feed B")

    def test_items_isolated(self):
        r = self.client.get("/api/inventory/items", **get_auth_header(self.user_a))
        data = r.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["item_name"], "Feed A")
