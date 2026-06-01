"""
Tests for the Reports app.
Covers: Livestock summary, health report, inventory usage, financial overview,
date filtering, and owner isolation.
"""

import json
from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase, Client
from conftest import (
    create_test_user, create_test_livestock, get_auth_header,
    create_test_health_record, create_test_vaccination,
    create_test_inventory_item,
)
from inventory.models import InventoryTransaction


class LivestockSummaryReportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_test_user()
        self.headers = get_auth_header(self.user)
        self.url = "/api/reports/livestock-summary"
        create_test_livestock(self.user, tag_id="R-001", animal_type="cattle", weight=400)
        create_test_livestock(self.user, tag_id="R-002", animal_type="goat", weight=60, status="sick")

    def test_summary_report(self):
        r = self.client.get(self.url, **self.headers)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["report_type"], "livestock_summary")
        self.assertEqual(data["total_livestock"], 2)
        self.assertIsNotNone(data["average_weight"])

    def test_summary_with_date_filter(self):
        """Filtering by from_date and to_date works."""
        r = self.client.get(self.url, {
            "from_date": str(date.today() - timedelta(days=1)),
            "to_date": str(date.today()),
        }, **self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["total_livestock"], 2)

    def test_summary_future_date_returns_empty(self):
        """Filtering with a future from_date returns zero."""
        r = self.client.get(self.url, {
            "from_date": str(date.today() + timedelta(days=30)),
        }, **self.headers)
        self.assertEqual(r.json()["total_livestock"], 0)

    def test_summary_empty_farm(self):
        other = create_test_user(email="nofarm@example.com")
        r = self.client.get(self.url, **get_auth_header(other))
        data = r.json()
        self.assertEqual(data["total_livestock"], 0)
        self.assertIsNone(data["average_weight"])

    def test_unauthenticated(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 401)


class HealthReportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_test_user()
        self.headers = get_auth_header(self.user)
        self.url = "/api/reports/health-report"
        animal = create_test_livestock(self.user)
        create_test_health_record(self.user, animal, condition="Foot rot")
        create_test_health_record(self.user, animal, condition="Mastitis")
        create_test_vaccination(self.user, animal, status="pending")
        create_test_vaccination(self.user, animal, vaccine_name="Done Vax", status="completed",
                                scheduled_date=date.today())

    def test_health_report(self):
        r = self.client.get(self.url, **self.headers)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["report_type"], "health_report")
        self.assertEqual(data["health_records"]["total"], 2)
        self.assertEqual(data["vaccinations"]["total"], 2)

    def test_health_report_with_date_filter(self):
        r = self.client.get(self.url, {
            "from_date": str(date.today()),
            "to_date": str(date.today()),
        }, **self.headers)
        self.assertEqual(r.status_code, 200)

    def test_health_report_owner_isolation(self):
        other = create_test_user(email="other_health@example.com")
        r = self.client.get(self.url, **get_auth_header(other))
        data = r.json()
        self.assertEqual(data["health_records"]["total"], 0)
        self.assertEqual(data["vaccinations"]["total"], 0)


class InventoryUsageReportTests(TestCase):
    """Tests for GET /api/reports/inventory-usage."""

    def setUp(self):
        self.client = Client()
        self.user = create_test_user()
        self.headers = get_auth_header(self.user)
        self.url = "/api/reports/inventory-usage"
        # Create items in different states
        self.feed = create_test_inventory_item(
            self.user, item_name="Feed", category="feed",
            quantity=Decimal("100"), min_stock_level=Decimal("10"),
            cost_per_unit=Decimal("250"),
        )
        self.medicine = create_test_inventory_item(
            self.user, item_name="Medicine", category="medicine",
            quantity=Decimal("3"), min_stock_level=Decimal("5"),
            cost_per_unit=Decimal("50"),
        )
        # Create transactions
        InventoryTransaction.objects.create(
            item=self.feed, transaction_type="add", quantity=Decimal("50"),
        )
        InventoryTransaction.objects.create(
            item=self.feed, transaction_type="use", quantity=Decimal("20"),
        )

    def test_inventory_usage_report(self):
        r = self.client.get(self.url, **self.headers)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["report_type"], "inventory_usage")
        self.assertEqual(data["items"]["total"], 2)
        self.assertEqual(data["transactions"]["total"], 2)

    def test_items_by_category(self):
        r = self.client.get(self.url, **self.headers)
        data = r.json()
        categories = {c["category"]: c["count"] for c in data["items"]["by_category"]}
        self.assertEqual(categories["feed"], 1)
        self.assertEqual(categories["medicine"], 1)

    def test_low_stock_alerts(self):
        """Medicine is below min_stock_level and should appear in alerts."""
        r = self.client.get(self.url, **self.headers)
        data = r.json()
        alerts = data["items"]["low_stock_alerts"]
        alert_names = [a["item_name"] for a in alerts]
        self.assertIn("Medicine", alert_names)
        self.assertNotIn("Feed", alert_names)

    def test_transaction_totals(self):
        r = self.client.get(self.url, **self.headers)
        data = r.json()
        self.assertEqual(float(data["transactions"]["total_added"]), 50.0)
        self.assertEqual(float(data["transactions"]["total_used"]), 20.0)

    def test_date_filter(self):
        """Future from_date returns zero transactions but still shows items."""
        r = self.client.get(self.url, {
            "from_date": str(date.today() + timedelta(days=30)),
        }, **self.headers)
        data = r.json()
        self.assertEqual(data["transactions"]["total"], 0)
        # Items are not date-filtered
        self.assertEqual(data["items"]["total"], 2)

    def test_empty_for_other_user(self):
        other = create_test_user(email="other_inv@example.com")
        r = self.client.get(self.url, **get_auth_header(other))
        data = r.json()
        self.assertEqual(data["items"]["total"], 0)
        self.assertEqual(data["transactions"]["total"], 0)

    def test_unauthenticated(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 401)


class FinancialOverviewReportTests(TestCase):
    """Tests for GET /api/reports/financial-overview."""

    def setUp(self):
        self.client = Client()
        self.user = create_test_user()
        self.headers = get_auth_header(self.user)
        self.url = "/api/reports/financial-overview"
        # Feed: 100 bags × 250 = 25,000
        self.feed = create_test_inventory_item(
            self.user, item_name="Feed", category="feed",
            quantity=Decimal("100"), min_stock_level=Decimal("10"),
            cost_per_unit=Decimal("250"),
        )
        # Medicine: 20 bottles × 50 = 1,000
        self.medicine = create_test_inventory_item(
            self.user, item_name="Medicine", category="medicine",
            quantity=Decimal("20"), min_stock_level=Decimal("5"),
            cost_per_unit=Decimal("50"),
        )
        # Transactions
        InventoryTransaction.objects.create(
            item=self.feed, transaction_type="add", quantity=Decimal("30"),
        )
        InventoryTransaction.objects.create(
            item=self.feed, transaction_type="use", quantity=Decimal("10"),
        )
        InventoryTransaction.objects.create(
            item=self.medicine, transaction_type="add", quantity=Decimal("5"),
        )

    def test_financial_overview_report(self):
        r = self.client.get(self.url, **self.headers)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["report_type"], "financial_overview")

    def test_inventory_valuation(self):
        r = self.client.get(self.url, **self.headers)
        data = r.json()
        # 100×250 + 20×50 = 26,000
        self.assertEqual(data["inventory_valuation"]["total_value"], 26000.0)

    def test_valuation_by_category(self):
        r = self.client.get(self.url, **self.headers)
        data = r.json()
        by_cat = {c["category"]: c["value"] for c in data["inventory_valuation"]["by_category"]}
        self.assertEqual(by_cat["feed"], 25000.0)
        self.assertEqual(by_cat["medicine"], 1000.0)

    def test_transaction_costs(self):
        r = self.client.get(self.url, **self.headers)
        data = r.json()
        costs = data["transaction_costs"]
        # additions: 30×250 + 5×50 = 7,750
        self.assertEqual(costs["total_addition_cost"], 7750.0)
        # usage: 10×250 = 2,500
        self.assertEqual(costs["total_usage_cost"], 2500.0)
        # net: 7750 - 2500 = 5,250
        self.assertEqual(costs["net_cost"], 5250.0)

    def test_date_filter_future(self):
        """Future from_date returns zero transaction costs."""
        r = self.client.get(self.url, {
            "from_date": str(date.today() + timedelta(days=30)),
        }, **self.headers)
        data = r.json()
        self.assertEqual(data["transaction_costs"]["total_addition_cost"], 0.0)
        self.assertEqual(data["transaction_costs"]["total_usage_cost"], 0.0)
        # Valuation is still current (not date-filtered)
        self.assertEqual(data["inventory_valuation"]["total_value"], 26000.0)

    def test_no_cost_items_excluded(self):
        """Items without cost_per_unit don't affect valuation."""
        create_test_inventory_item(
            self.user, item_name="Free Tool", category="equipment",
            quantity=Decimal("5"), min_stock_level=Decimal("1"),
            cost_per_unit=None,
        )
        r = self.client.get(self.url, **self.headers)
        data = r.json()
        # Still 26,000 — free tool excluded
        self.assertEqual(data["inventory_valuation"]["total_value"], 26000.0)

    def test_empty_for_other_user(self):
        other = create_test_user(email="other_fin@example.com")
        r = self.client.get(self.url, **get_auth_header(other))
        data = r.json()
        self.assertEqual(data["inventory_valuation"]["total_value"], 0.0)
        self.assertEqual(data["transaction_costs"]["total_addition_cost"], 0.0)

    def test_unauthenticated(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 401)

