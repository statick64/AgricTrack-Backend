from datetime import date
from decimal import Decimal
from typing import List, Optional

from django.db.models import Avg, Count, F, Sum
from ninja import Router

from accounts.api import AuthBearer

router = Router()


@router.get("/livestock-summary", auth=AuthBearer())
def livestock_summary_report(
    request, from_date: Optional[date] = None, to_date: Optional[date] = None
):
    """Generate livestock summary report"""
    from livestock.models import Livestock

    queryset = Livestock.objects.filter(owner=request.auth)

    if from_date:
        # Using __date to compare DateTimeField with date
        queryset = queryset.filter(created_at__date__gte=from_date)
    if to_date:
        queryset = queryset.filter(created_at__date__lte=to_date)

    total = queryset.count()
    by_type = queryset.values("animal_type").annotate(count=Count("id"))
    by_status = queryset.values("status").annotate(count=Count("id"))
    avg_weight = queryset.aggregate(avg_weight=Avg("weight"))

    return {
        "report_type": "livestock_summary",
        "period": {"from": from_date, "to": to_date},
        "total_livestock": total,
        "breakdown_by_type": list(by_type),
        "breakdown_by_status": list(by_status),
        "average_weight": avg_weight["avg_weight"],
    }


@router.get("/health-report", auth=AuthBearer())
def health_report(
    request, from_date: Optional[date] = None, to_date: Optional[date] = None
):
    """Generate health report"""
    from health.models import HealthRecord, VaccinationRecord

    health_records = HealthRecord.objects.filter(owner=request.auth)
    vaccinations = VaccinationRecord.objects.filter(owner=request.auth)

    if from_date:
        health_records = health_records.filter(date__gte=from_date)
        vaccinations = vaccinations.filter(scheduled_date__gte=from_date)

    if to_date:
        health_records = health_records.filter(date__lte=to_date)
        vaccinations = vaccinations.filter(scheduled_date__lte=to_date)

    total_records = health_records.count()
    records_by_condition = health_records.values("condition").annotate(
        count=Count("id")
    )

    total_vaccinations = vaccinations.count()
    vaccinations_by_status = vaccinations.values("status").annotate(count=Count("id"))

    return {
        "report_type": "health_report",
        "period": {"from": from_date, "to": to_date},
        "health_records": {
            "total": total_records,
            "by_condition": list(records_by_condition),
        },
        "vaccinations": {
            "total": total_vaccinations,
            "by_status": list(vaccinations_by_status),
        },
    }


@router.get("/inventory-usage", auth=AuthBearer())
def inventory_usage_report(
    request, from_date: Optional[date] = None, to_date: Optional[date] = None
):
    """Generate inventory usage report with item summaries and transaction breakdown."""
    from inventory.models import InventoryItem, InventoryTransaction

    items = InventoryItem.objects.filter(owner=request.auth)
    transactions = InventoryTransaction.objects.filter(item__owner=request.auth)

    if from_date:
        transactions = transactions.filter(transaction_date__date__gte=from_date)
    if to_date:
        transactions = transactions.filter(transaction_date__date__lte=to_date)

    # Item summaries
    total_items = items.count()
    by_category = list(
        items.values("category").annotate(count=Count("id"))
    )
    by_status = list(
        items.values("status").annotate(count=Count("id"))
    )
    low_stock_items = list(
        items.filter(status__in=["low_stock", "out_of_stock"]).values(
            "id", "item_name", "category", "quantity", "unit", "status"
        )
    )

    # Transaction summaries
    total_transactions = transactions.count()
    additions = transactions.filter(transaction_type="add").aggregate(
        total_qty=Sum("quantity")
    )
    usage = transactions.filter(transaction_type="use").aggregate(
        total_qty=Sum("quantity")
    )
    by_transaction_type = list(
        transactions.values("transaction_type").annotate(
            count=Count("id"), total_quantity=Sum("quantity")
        )
    )

    return {
        "report_type": "inventory_usage",
        "period": {"from": from_date, "to": to_date},
        "items": {
            "total": total_items,
            "by_category": by_category,
            "by_status": by_status,
            "low_stock_alerts": low_stock_items,
        },
        "transactions": {
            "total": total_transactions,
            "total_added": additions["total_qty"] or Decimal("0"),
            "total_used": usage["total_qty"] or Decimal("0"),
            "by_type": by_transaction_type,
        },
    }


@router.get("/financial-overview", auth=AuthBearer())
def financial_overview_report(
    request, from_date: Optional[date] = None, to_date: Optional[date] = None
):
    """Generate financial overview report with inventory valuation and transaction costs."""
    from inventory.models import InventoryItem, InventoryTransaction

    items = InventoryItem.objects.filter(owner=request.auth)
    transactions = InventoryTransaction.objects.filter(item__owner=request.auth)

    if from_date:
        transactions = transactions.filter(transaction_date__date__gte=from_date)
    if to_date:
        transactions = transactions.filter(transaction_date__date__lte=to_date)

    # Current inventory valuation (quantity × cost_per_unit for items with a cost)
    valued_items = items.filter(cost_per_unit__isnull=False)
    total_value = valued_items.aggregate(
        total=Sum(F("quantity") * F("cost_per_unit"))
    )["total"] or Decimal("0")

    value_by_category = list(
        valued_items.values("category").annotate(
            value=Sum(F("quantity") * F("cost_per_unit")),
            item_count=Count("id"),
        )
    )

    # Transaction costs (join to item's cost_per_unit)
    costed_txns = transactions.filter(item__cost_per_unit__isnull=False)

    addition_cost = costed_txns.filter(transaction_type="add").aggregate(
        total=Sum(F("quantity") * F("item__cost_per_unit"))
    )["total"] or Decimal("0")

    usage_cost = costed_txns.filter(transaction_type="use").aggregate(
        total=Sum(F("quantity") * F("item__cost_per_unit"))
    )["total"] or Decimal("0")

    # Per-category transaction cost breakdown
    cost_by_category = list(
        costed_txns.values("item__category").annotate(
            total_cost=Sum(F("quantity") * F("item__cost_per_unit")),
            transaction_count=Count("id"),
        )
    )

    return {
        "report_type": "financial_overview",
        "period": {"from": from_date, "to": to_date},
        "inventory_valuation": {
            "total_value": float(total_value),
            "by_category": [
                {
                    "category": c["category"],
                    "value": float(c["value"]),
                    "item_count": c["item_count"],
                }
                for c in value_by_category
            ],
        },
        "transaction_costs": {
            "total_addition_cost": float(addition_cost),
            "total_usage_cost": float(usage_cost),
            "net_cost": float(addition_cost - usage_cost),
            "by_category": [
                {
                    "category": c["item__category"],
                    "total_cost": float(c["total_cost"]),
                    "transaction_count": c["transaction_count"],
                }
                for c in cost_by_category
            ],
        },
    }


# ---------------------------------------------------------------------------
# Export endpoints – full individual records for PDF export
# ---------------------------------------------------------------------------

@router.get("/export/livestock", auth=AuthBearer())
def export_livestock(
    request, from_date: Optional[date] = None, to_date: Optional[date] = None
):
    """Export full individual livestock records for PDF generation."""
    from livestock.models import Livestock

    queryset = Livestock.objects.filter(owner=request.auth)

    if from_date:
        queryset = queryset.filter(created_at__date__gte=from_date)
    if to_date:
        queryset = queryset.filter(created_at__date__lte=to_date)

    records = [
        {
            "id": str(animal.id),
            "tag_id": animal.tag_id,
            "name": animal.name,
            "animal_type": animal.animal_type,
            "breed": animal.breed,
            "gender": animal.gender,
            "date_of_birth": animal.date_of_birth,
            "age": animal.age,
            "weight": float(animal.weight),
            "status": animal.status,
            "notes": animal.notes,
            "created_at": animal.created_at,
            "updated_at": animal.updated_at,
        }
        for animal in queryset
    ]

    return {
        "report_type": "livestock_export",
        "period": {"from": from_date, "to": to_date},
        "total": len(records),
        "records": records,
    }


@router.get("/export/health", auth=AuthBearer())
def export_health(
    request, from_date: Optional[date] = None, to_date: Optional[date] = None
):
    """Export full individual health and vaccination records for PDF generation."""
    from health.models import HealthRecord, VaccinationRecord

    health_qs = HealthRecord.objects.filter(owner=request.auth).select_related("animal")
    vaccination_qs = VaccinationRecord.objects.filter(owner=request.auth).select_related("animal")

    if from_date:
        health_qs = health_qs.filter(date__gte=from_date)
        vaccination_qs = vaccination_qs.filter(scheduled_date__gte=from_date)
    if to_date:
        health_qs = health_qs.filter(date__lte=to_date)
        vaccination_qs = vaccination_qs.filter(scheduled_date__lte=to_date)

    health_records = [
        {
            "id": record.id,
            "animal_tag_id": record.animal.tag_id,
            "animal_name": record.animal.name,
            "animal_type": record.animal.animal_type,
            "date": record.date,
            "condition": record.condition,
            "treatment": record.treatment,
            "veterinarian": record.veterinarian,
            "status": record.status,
            "notes": record.notes,
            "follow_up_date": record.follow_up_date,
            "created_at": record.created_at,
        }
        for record in health_qs
    ]

    vaccination_records = [
        {
            "id": vax.id,
            "animal_tag_id": vax.animal.tag_id if vax.animal else None,
            "animal_name": vax.animal.name if vax.animal else None,
            "group_name": vax.group_name,
            "vaccine_name": vax.vaccine_name,
            "scheduled_date": vax.scheduled_date,
            "administered_date": vax.administered_date,
            "administered_by": vax.administered_by,
            "batch_number": vax.batch_number,
            "status": vax.status,
            "notes": vax.notes,
            "created_at": vax.created_at,
        }
        for vax in vaccination_qs
    ]

    return {
        "report_type": "health_export",
        "period": {"from": from_date, "to": to_date},
        "health_records": {
            "total": len(health_records),
            "records": health_records,
        },
        "vaccination_records": {
            "total": len(vaccination_records),
            "records": vaccination_records,
        },
    }


@router.get("/export/inventory", auth=AuthBearer())
def export_inventory(
    request, from_date: Optional[date] = None, to_date: Optional[date] = None
):
    """Export full individual inventory items and transaction records for PDF generation."""
    from inventory.models import InventoryItem, InventoryTransaction

    items_qs = InventoryItem.objects.filter(owner=request.auth)
    transactions_qs = InventoryTransaction.objects.filter(
        item__owner=request.auth
    ).select_related("item")

    if from_date:
        transactions_qs = transactions_qs.filter(transaction_date__date__gte=from_date)
    if to_date:
        transactions_qs = transactions_qs.filter(transaction_date__date__lte=to_date)

    items = [
        {
            "id": item.id,
            "item_name": item.item_name,
            "category": item.category,
            "quantity": float(item.quantity),
            "unit": item.unit,
            "min_stock_level": float(item.min_stock_level),
            "status": item.status,
            "description": item.description,
            "supplier": item.supplier,
            "cost_per_unit": float(item.cost_per_unit) if item.cost_per_unit is not None else None,
            "total_value": (
                float(item.quantity * item.cost_per_unit)
                if item.cost_per_unit is not None
                else None
            ),
            "created_at": item.created_at,
            "last_updated": item.last_updated,
        }
        for item in items_qs
    ]

    transactions = [
        {
            "id": txn.id,
            "item_id": txn.item.id,
            "item_name": txn.item.item_name,
            "category": txn.item.category,
            "transaction_type": txn.transaction_type,
            "quantity": float(txn.quantity),
            "unit": txn.item.unit,
            "cost_per_unit": (
                float(txn.item.cost_per_unit) if txn.item.cost_per_unit is not None else None
            ),
            "total_cost": (
                float(txn.quantity * txn.item.cost_per_unit)
                if txn.item.cost_per_unit is not None
                else None
            ),
            "notes": txn.notes,
            "transaction_date": txn.transaction_date,
        }
        for txn in transactions_qs
    ]

    return {
        "report_type": "inventory_export",
        "period": {"from": from_date, "to": to_date},
        "items": {
            "total": len(items),
            "records": items,
        },
        "transactions": {
            "total": len(transactions),
            "records": transactions,
        },
    }


@router.get("/export/financial", auth=AuthBearer())
def export_financial(
    request, from_date: Optional[date] = None, to_date: Optional[date] = None
):
    """Export full financial records (per-item valuation and costed transactions) for PDF generation."""
    from inventory.models import InventoryItem, InventoryTransaction

    items_qs = InventoryItem.objects.filter(owner=request.auth)
    transactions_qs = InventoryTransaction.objects.filter(
        item__owner=request.auth, item__cost_per_unit__isnull=False
    ).select_related("item")

    if from_date:
        transactions_qs = transactions_qs.filter(transaction_date__date__gte=from_date)
    if to_date:
        transactions_qs = transactions_qs.filter(transaction_date__date__lte=to_date)

    # Full per-item valuation snapshot (all items, even those without a cost)
    valued_items = [
        {
            "id": item.id,
            "item_name": item.item_name,
            "category": item.category,
            "quantity": float(item.quantity),
            "unit": item.unit,
            "cost_per_unit": (
                float(item.cost_per_unit) if item.cost_per_unit is not None else None
            ),
            "total_value": (
                float(item.quantity * item.cost_per_unit)
                if item.cost_per_unit is not None
                else None
            ),
            "status": item.status,
            "supplier": item.supplier,
            "last_updated": item.last_updated,
        }
        for item in items_qs
    ]

    # Full costed transaction records
    costed_transactions = [
        {
            "id": txn.id,
            "item_name": txn.item.item_name,
            "category": txn.item.category,
            "transaction_type": txn.transaction_type,
            "quantity": float(txn.quantity),
            "unit": txn.item.unit,
            "cost_per_unit": float(txn.item.cost_per_unit),
            "total_cost": float(txn.quantity * txn.item.cost_per_unit),
            "notes": txn.notes,
            "transaction_date": txn.transaction_date,
        }
        for txn in transactions_qs
    ]

    # Aggregate totals
    total_inventory_value = sum(
        (i["total_value"] or 0) for i in valued_items if i["cost_per_unit"] is not None
    )
    total_addition_cost = sum(
        t["total_cost"] for t in costed_transactions if t["transaction_type"] == "add"
    )
    total_usage_cost = sum(
        t["total_cost"] for t in costed_transactions if t["transaction_type"] == "use"
    )

    return {
        "report_type": "financial_export",
        "period": {"from": from_date, "to": to_date},
        "summary": {
            "total_inventory_value": total_inventory_value,
            "total_addition_cost": total_addition_cost,
            "total_usage_cost": total_usage_cost,
            "net_cost": total_addition_cost - total_usage_cost,
        },
        "inventory_valuation": {
            "total": len(valued_items),
            "records": valued_items,
        },
        "costed_transactions": {
            "total": len(costed_transactions),
            "records": costed_transactions,
        },
    }
