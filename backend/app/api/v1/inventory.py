from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.inventory.inventory_service import InventoryService


router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.post("/{domain}")
def run_inventory(domain: str, db: Session = Depends(get_db)):
    try:
        snapshot = InventoryService(db).run_domain_inventory(domain)
        return {
            "status": snapshot.status,
            "snapshot_id": snapshot.id,
            "scope_id": snapshot.scope_id,
            "domain": domain.strip().lower().rstrip("."),
            "started_at": snapshot.started_at,
            "completed_at": snapshot.completed_at,
        }
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inventory failed: {exc}") from exc
