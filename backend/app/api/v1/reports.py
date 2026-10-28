from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.report_service import ReportService


router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/security")
def security_report(
    days: int = Query(default=7, ge=1, le=90),
    scope_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return ReportService(db).build_security_report(days=days, scope_id=scope_id)
