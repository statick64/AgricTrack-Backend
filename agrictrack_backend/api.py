from ninja import NinjaAPI

from accounts.api import router as accounts_router
from health.api import router as health_router
from inventory.api import router as inventory_router
from livestock.api import router as livestock_router
from reports.api import router as reports_router
from training.api import router as training_router

api = NinjaAPI(
    title="AgricTrack API",
    version="1.0.0",
    description="REST API for AgricTrack Livestock Management System",
)

# Register routers
api.add_router("/auth/", accounts_router, tags=["Authentication"])
api.add_router("/livestock/", livestock_router, tags=["Livestock"])
api.add_router("/health/", health_router, tags=["Health & Vaccination"])
api.add_router("/inventory/", inventory_router, tags=["Inventory"])
api.add_router("/reports/", reports_router, tags=["Reports"])
api.add_router("/training/", training_router, tags=["Training"])
