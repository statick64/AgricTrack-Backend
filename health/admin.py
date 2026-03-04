from django.contrib import admin
from .models import  HealthRecord, VaccinationRecord  

# Register your models here.

admin.site.register(HealthRecord)
admin.site.register(VaccinationRecord)