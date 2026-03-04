from django.conf import settings
from django.db import models

from livestock.models import Livestock


class HealthRecord(models.Model):
    """Health records for individual animals"""

    STATUS_CHOICES = [
        ("ongoing", "Ongoing"),
        ("recovered", "Recovered"),
        ("healthy", "Healthy"),
    ]

    # Relations
    animal = models.ForeignKey(
        Livestock, on_delete=models.CASCADE, related_name="health_records"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="health_records",
    )

    # Record Details
    date = models.DateField()
    condition = models.CharField(max_length=200)
    treatment = models.TextField()
    veterinarian = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    # Additional Info
    notes = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "health_records"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.animal.tag_id} - {self.condition} ({self.date})"


class VaccinationRecord(models.Model):
    """Vaccination schedules and records"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("overdue", "Overdue"),
    ]

    # Relations
    animal = models.ForeignKey(
        Livestock,
        on_delete=models.CASCADE,
        related_name="vaccinations",
        null=True,
        blank=True,
    )
    group_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="For group vaccinations (e.g., 'Herd A')",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vaccinations",
    )

    # Vaccination Details
    vaccine_name = models.CharField(max_length=200)
    scheduled_date = models.DateField()
    administered_date = models.DateField(null=True, blank=True)
    administered_by = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Additional Info
    batch_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "vaccination_records"
        ordering = ["-scheduled_date"]

    def __str__(self):
        target = self.animal.tag_id if self.animal else self.group_name
        return f"{target} - {self.vaccine_name} ({self.scheduled_date})"
