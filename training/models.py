from django.db import models


class TrainingResource(models.Model):
    """Educational resources and articles for farmers"""

    CATEGORY_CHOICES = [
        ("animal_health", "Animal Health"),
        ("farm_management", "Farm Management"),
        ("market_info", "Market Info"),
        ("nutrition", "Nutrition"),
        ("government_programs", "Government Programs"),
    ]

    # Content
    title = models.CharField(max_length=300)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    description = models.TextField()
    content = models.TextField()

    # Media
    featured_image = models.ImageField(upload_to="training/", null=True, blank=True)
    external_link = models.URLField(blank=True)

    # Metadata
    read_time = models.IntegerField(help_text="Estimated read time in minutes")
    is_featured = models.BooleanField(default=False)
    published_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "training_resources"
        ordering = ["-published_date"]

    def __str__(self):
        return self.title
