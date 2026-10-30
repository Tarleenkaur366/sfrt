from app.routers.auth import router as auth_router
from app.routers.categories import router as categories_router
from app.routers.transactions import router as transactions_router
from app.routers.income import router as income_router
from app.routers.expenses import router as expenses_router
from app.routers.dashboard import router as dashboard_router
from app.routers.reports import router as reports_router
from app.routers.analytics import router as analytics_router
from app.routers.imports import router as imports_router
from app.routers.insights import router as insights_router

__all__ = [
    "auth_router",
    "categories_router",
    "transactions_router",
    "income_router",
    "expenses_router",
    "dashboard_router",
    "reports_router",
    "analytics_router",
    "imports_router",
    "insights_router"
]
