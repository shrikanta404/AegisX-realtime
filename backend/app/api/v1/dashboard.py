from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.change import Change
from app.models.finding import Finding
from app.models.inventory import InventorySnapshot
from app.models.scope import AuthorizedScope
from app.services.asset_service import AssetService
from app.services.scheduler_service import scheduler


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    assets = AssetService(db).summary()
    active_scopes = db.scalar(
        select(func.count(AuthorizedScope.id)).where(AuthorizedScope.is_active.is_(True))
    ) or 0
    open_findings = db.scalar(
        select(func.count(Finding.id)).where(
            Finding.status == "open",
            Finding.false_positive.is_(False),
        )
    ) or 0
    high_priority = db.scalar(
        select(func.count(Finding.id)).where(
            Finding.status == "open",
            Finding.false_positive.is_(False),
            Finding.severity.in_(["critical", "high"]),
        )
    ) or 0

    cutoff = datetime.utcnow() - timedelta(days=7)
    recent_changes = db.scalar(
        select(func.count(Change.id)).where(Change.detected_at >= cutoff)
    ) or 0
    latest_snapshot = db.scalar(
        select(InventorySnapshot.completed_at)
        .where(InventorySnapshot.status == "completed")
        .order_by(InventorySnapshot.completed_at.desc())
        .limit(1)
    )

    findings = db.scalars(
        select(Finding)
        .order_by(Finding.created_at.desc())
        .limit(8)
    ).all()
    changes = db.scalars(
        select(Change)
        .order_by(Change.detected_at.desc())
        .limit(8)
    ).all()

    events = []
    for item in findings:
        events.append({
            "type": "finding",
            "id": item.id,
            "title": item.title,
            "asset_identifier": item.asset_identifier,
            "severity": item.severity,
            "timestamp": item.created_at,
        })
    for item in changes:
        events.append({
            "type": "change",
            "id": item.id,
            "title": item.change_type.replace("_", " ").title(),
            "asset_identifier": item.asset_identifier,
            "severity": "info",
            "timestamp": item.detected_at,
        })
    events.sort(key=lambda row: row["timestamp"], reverse=True)

    return {
        "scope_count": active_scopes,
        "assets": assets,
        "open_findings": open_findings,
        "high_priority_findings": high_priority,
        "recent_changes": recent_changes,
        "last_scan_at": latest_snapshot,
        "scheduler": {
            "running": scheduler.running,
            "job_count": len(scheduler.get_jobs()),
        },
        "recent_events": events[:10],
    }
