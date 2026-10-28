from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.scope import AuthorizedScope
from app.services.change_detection_service import ChangeDetectionService
from app.services.monitoring_service import MonitoringService
from app.services.scope_guard import ScopeGuard


router = APIRouter(prefix="/changes", tags=["Change Detection"])


@router.get("")
def list_changes(
    scope_id: int | None = Query(default=None),
    domain: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    rows = ChangeDetectionService(db).list_changes(scope_id=scope_id, domain=domain, limit=limit)
    return [
        {
            "id": row.id,
            "snapshot_id": row.snapshot_id,
            "asset_type": row.asset_type,
            "asset_identifier": row.asset_identifier,
            "change_type": row.change_type,
            "previous_state": row.previous_state,
            "current_state": row.current_state,
            "detected_at": row.detected_at,
        }
        for row in rows
    ]


@router.post("/{domain}")
def detect_changes(domain: str, db: Session = Depends(get_db)):
    normalized_domain = ScopeGuard.normalize_domain(domain)
    scope = ScopeGuard(db).get_scope_for_domain(normalized_domain)
    if scope is None:
        raise HTTPException(
            status_code=403,
            detail=f"Target '{domain}' is not covered by an active authorized scope.",
        )
    return MonitoringService(db).run(normalized_domain, actor="api")
