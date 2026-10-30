import logging
import time
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings, ROOT_DIR
from app.database import init_db
from app.routers import (
    auth_router,
    categories_router,
    transactions_router,
    income_router,
    expenses_router,
    dashboard_router,
    reports_router,
    analytics_router,
    imports_router,
    insights_router
)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sfrt.main")

# Initialize database schema safely
init_db()

app = FastAPI(
    title=settings.APP_NAME,
    description="Smart Financial Reporting Tool (SFRT) - Enterprise financial intelligence and reporting platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Timing & Diagnostic Logging Middleware (Sanitized)
@app.middleware("http")
async def log_and_time_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    # Avoid logging sensitive path payloads
    logger.info(f"{request.method} {request.url.path} - {response.status_code} ({duration_ms:.1f}ms)")
    return response

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error processing {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later or contact support."}
    )

# Health-Check Endpoint
@app.get("/api/v1/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time()
    }

# Register API Routers under /api/v1
api_v1_prefix = "/api/v1"
app.include_router(auth_router, prefix=api_v1_prefix)
app.include_router(categories_router, prefix=api_v1_prefix)
app.include_router(transactions_router, prefix=api_v1_prefix)
app.include_router(income_router, prefix=api_v1_prefix)
app.include_router(expenses_router, prefix=api_v1_prefix)
app.include_router(dashboard_router, prefix=api_v1_prefix)
app.include_router(reports_router, prefix=api_v1_prefix)
app.include_router(analytics_router, prefix=api_v1_prefix)
app.include_router(imports_router, prefix=api_v1_prefix)
app.include_router(insights_router, prefix=api_v1_prefix)

# Mount frontend directory for seamless serving
frontend_dir = ROOT_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dir / "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    def serve_index():
        return FileResponse(frontend_dir / "index.html")

    @app.get("/{page}.html", include_in_schema=False)
    def serve_html_page(page: str):
        page_path = frontend_dir / f"{page}.html"
        if page_path.exists():
            return FileResponse(page_path)
        return JSONResponse(status_code=404, content={"detail": "Page not found"})
