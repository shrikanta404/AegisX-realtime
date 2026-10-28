from datetime import datetime

from sqlalchemy.orm import Session

from app.models.finding import Finding
from app.services.audit_service import AuditService


class FindingReviewService:
    def __init__(self, db: Session):
        self.db = db

    def mark_false_positive(self, finding_id: int, reason: str, actor: str | None = None) -> Finding:
        finding = self.db.query(Finding).filter(Finding.id == finding_id).first()
        if finding is None:
            raise ValueError(f"Finding {finding_id} was not found.")
        if not reason.strip():
            raise ValueError("A false-positive reason is required.")

        finding.false_positive = True
        finding.false_positive_reason = reason.strip()
        finding.status = "closed"
        finding.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(finding)

        AuditService(self.db).log(
            action="finding_marked_false_positive",
            target=str(finding.id),
            actor=actor,
            details={"asset_identifier": finding.asset_identifier, "reason": finding.false_positive_reason},
        )
        return finding
