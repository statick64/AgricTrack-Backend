from django.contrib import admin
from .models import InventoryItem, InventoryTransaction
# Register your models here.


admin.site.register(InventoryItem)
admin.site.register(InventoryTransaction)