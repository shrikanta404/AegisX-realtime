from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.scope import AuthorizedScope
from app.schemas.scope import ScopeCreate, ScopeResponse, ScopeUpdate
from app.services.audit_service import AuditService


router = APIRouter(prefix="/scopes", tags=["Authorized Scopes"])


@router.post("", response_model=ScopeResponse, status_code=status.HTTP_201_CREATED)
def create_scope(
    scope_data: ScopeCreate,
    x_actor: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    active_count = db.scalar(
        select(func.count(AuthorizedScope.id)).where(AuthorizedScope.is_active.is_(True))
    ) or 0
    if active_count >= settings.max_authorized_domains:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The authorized domain limit of {settings.max_authorized_domains} has been reached.",
        )

    existing = db.scalar(
        select(AuthorizedScope).where(func.lower(AuthorizedScope.domain) == scope_data.domain.lower())
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A scope with this domain already exists.")

    scope = AuthorizedScope(
        name=scope_data.name,
        domain=scope_data.domain,
        allowed_ports=scope_data.allowed_ports,
        allowed_checks=scope_data.allowed_checks,
        description=scope_data.description,
        is_active=True,
    )
    db.add(scope)
    db.commit()
    db.refresh(scope)
    AuditService(db).log("scope_created", target=scope.domain, actor=x_actor, details={"scope_id": scope.id})
    return scope


@router.get("", response_model=list[ScopeResponse])
def list_scopes(db: Session = Depends(get_db)):
    return db.scalars(select(AuthorizedScope).order_by(AuthorizedScope.id.desc())).all()


@router.get("/{scope_id}", response_model=ScopeResponse)
def get_scope(scope_id: int, db: Session = Depends(get_db)):
    scope = db.get(AuthorizedScope, scope_id)
    if scope is None:
        raise HTTPException(status_code=404, detail="Scope not found.")
    return scope


@router.patch("/{scope_id}", response_model=ScopeResponse)
def update_scope(
    scope_id: int,
    scope_data: ScopeUpdate,
    x_actor: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    scope = db.get(AuthorizedScope, scope_id)
    if scope is None:
        raise HTTPException(status_code=404, detail="Scope not found.")

    update_data = scope_data.model_dump(exclude_unset=True)
    if "domain" in update_data:
        existing = db.scalar(
            select(AuthorizedScope).where(
                func.lower(AuthorizedScope.domain) == update_data["domain"].lower(),
                AuthorizedScope.id != scope_id,
            )
        )
        if existing:
            raise HTTPException(status_code=409, detail="A scope with this domain already exists.")

    for field, value in update_data.items():
        setattr(scope, field, value)
    scope.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(scope)
    AuditService(db).log("scope_updated", target=scope.domain, actor=x_actor, details={"scope_id": scope.id, "fields": list(update_data)})
    return scope


@router.delete("/{scope_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_scope(
    scope_id: int,
    x_actor: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    scope = db.get(AuthorizedScope, scope_id)
    if scope is None:
        raise HTTPException(status_code=404, detail="Scope not found.")
    scope.is_active = False
    scope.updated_at = datetime.utcnow()
    db.commit()
    AuditService(db).log("scope_deactivated", target=scope.domain, actor=x_actor, details={"scope_id": scope.id})
    return None
