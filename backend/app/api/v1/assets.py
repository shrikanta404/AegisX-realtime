from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.asset_service import AssetService


router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get("")
def list_assets(
    scope_id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    service = AssetService(db)
    return {
        "summary": service.summary(scope_id=scope_id),
        "assets": service.list_assets(scope_id=scope_id, search=search),
    }
