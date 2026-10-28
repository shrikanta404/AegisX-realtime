from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.audit import AuditLog


router = APIRouter(prefix="/audit", tags=["Audit Log"])


@router.get("")
def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    ).all()
    return [
        {
            "id": row.id,
            "action": row.action,
            "target": row.target,
            "actor": row.actor,
            "details": row.details,
            "created_at": row.created_at,
        }
        for row in rows
    ]
