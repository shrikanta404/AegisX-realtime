import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        action: str,
        target: str | None = None,
        actor: str | None = None,
        details: Any | None = None,
        commit: bool = True,
    ) -> AuditLog:
        if details is None:
            serialized = None
        elif isinstance(details, str):
            serialized = details
        else:
            serialized = json.dumps(details, default=str)

        item = AuditLog(
            action=action,
            target=target,
            actor=actor,
            details=serialized,
        )
        self.db.add(item)
        if commit:
            self.db.commit()
            self.db.refresh(item)
        return item
