from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.ai import router as ai_router
from app.api.v1.ai_analysis import router as ai_analysis_router
from app.api.v1.assets import router as assets_router
from app.api.v1.audit import router as audit_router
from app.api.v1.change_detection import router as changes_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.findings import router as findings_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.reports import router as reports_router
from app.api.v1.scheduler import router as scheduler_router
from app.api.v1.scopes import router as scopes_router
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.scheduler_service import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[AEGISX] Starting application...")
    start_scheduler()
    yield
    print("[AEGISX] Shutting down application...")
    stop_scheduler()


app = FastAPI(
    lifespan=lifespan,
    title=settings.app_name,
    version="2.0.0",
    description=(
        "AegisX authorized attack-surface inventory, continuous change monitoring, "
        "evidence collection and AI-assisted security analysis platform."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in [
    scopes_router,
    inventory_router,
    changes_router,
    findings_router,
    ai_router,
    ai_analysis_router,
    scheduler_router,
    dashboard_router,
    assets_router,
    reports_router,
    audit_router,
]:
    app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health():
    db_status = "healthy"
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
    except Exception as exc:
        db_status = f"error: {exc}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "aegisx-backend",
        "database": db_status,
        "scheduler": "running" if settings.scheduler_enabled else "disabled",
    }
