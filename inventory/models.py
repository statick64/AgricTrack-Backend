from django.conf import settings
from django.db import models


class InventoryItem(models.Model):
    """Inventory items like feed, medicine, equipment"""

    CATEGORY_CHOICES = [
        ("feed", "Feed"),
        ("medicine", "Medicine"),
        ("equipment", "Equipment"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("in_stock", "In Stock"),
        ("low_stock", "Low Stock"),
        ("out_of_stock", "Out of Stock"),
    ]

    # Ownership
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inventory_items",
    )

    # Item Details
    item_name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50)  # e.g., "Bags", "Bottles", "Units"
    min_stock_level = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Minimum quantity before low stock alert",
    )

    # Status (auto-calculated)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="in_stock")

    # Additional Info
    description = models.TextField(blank=True)
    supplier = models.CharField(max_length=200, blank=True)
    cost_per_unit = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    # Metadata
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inventory_items"
        ordering = ["item_name"]

    def __str__(self):
        return f"{self.item_name} ({self.quantity} {self.unit})"

    def save(self, *args, **kwargs):
        """Auto-update status based on quantity"""
        if self.quantity <= 0:
            self.status = "out_of_stock"
        elif self.quantity <= self.min_stock_level:
            self.status = "low_stock"
        else:
            self.status = "in_stock"
        super().save(*args, **kwargs)


class InventoryTransaction(models.Model):
    """Track inventory additions and usage"""

    TRANSACTION_TYPES = [
        ("add", "Addition"),
        ("use", "Usage"),
        ("adjust", "Adjustment"),
    ]

    item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE, related_name="transactions"
    )
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inventory_transactions"
        ordering = ["-transaction_date"]

    def __str__(self):
        return f"{self.transaction_type} - {self.item.item_name} ({self.quantity})"
