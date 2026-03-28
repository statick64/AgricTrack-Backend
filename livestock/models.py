from django.conf import settings
from django.db import models
import uuid


class Livestock(models.Model):
    """Model for individual livestock animals"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ANIMAL_TYPES = [
        ("cattle", "Cattle"),
        ("goat", "Goat"),
        ("sheep", "Sheep"),
        ("poultry", "Poultry"),
    ]

    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
    ]

    STATUS_CHOICES = [
        ("healthy", "Healthy"),
        ("sick", "Sick"),
        ("pregnant", "Pregnant"),
        ("quarantine", "Quarantine"),
    ]

    # Ownership
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="livestock",
    )

    # Basic Information
    tag_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100, blank=True)
    animal_type = models.CharField(max_length=20, choices=ANIMAL_TYPES)
    breed = models.CharField(max_length=100)

    # Physical Attributes
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    weight = models.DecimalField(
        max_digits=6, decimal_places=2, help_text="Weight in kg"
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="healthy")
    notes = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "livestock"
        ordering = ["-created_at"]
        verbose_name_plural = "Livestock"

    def __str__(self):
        return f"{self.tag_id} - {self.name or self.animal_type}"

    @property
    def age(self):
        """Calculate age from date of birth"""
        from datetime import date

        today = date.today()
        age = today.year - self.date_of_birth.year
        if today.month < self.date_of_birth.month or (
            today.month == self.date_of_birth.month
            and today.day < self.date_of_birth.day
        ):
            age -= 1
        return age
