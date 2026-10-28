from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.asset import Domain
from app.models.change import Change
from app.models.evidence import Evidence
from app.models.finding import Finding
from app.models.inventory import InventorySnapshot
from app.models.scope import AuthorizedScope


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def build_security_report(self, days: int = 7, scope_id: int | None = None) -> dict[str, Any]:
        days = max(1, min(days, 90))
        cutoff = datetime.utcnow() - timedelta(days=days)

        active_scope_query = select(func.count(AuthorizedScope.id)).where(AuthorizedScope.is_active.is_(True))
        if scope_id is not None:
            active_scope_query = active_scope_query.where(AuthorizedScope.id == scope_id)

        changes_query = (
            select(Change)
            .join(InventorySnapshot, Change.snapshot_id == InventorySnapshot.id)
            .where(Change.detected_at >= cutoff)
            .order_by(Change.detected_at.desc())
        )
        snapshots_query = (
            select(InventorySnapshot)
            .where(
                InventorySnapshot.status == "completed",
                InventorySnapshot.completed_at >= cutoff,
            )
            .order_by(InventorySnapshot.completed_at.desc())
        )

        if scope_id is not None:
            changes_query = changes_query.where(InventorySnapshot.scope_id == scope_id)
            snapshots_query = snapshots_query.where(InventorySnapshot.scope_id == scope_id)

        changes = self.db.scalars(changes_query.limit(200)).all()
        snapshots = self.db.scalars(snapshots_query.limit(200)).all()

        change_ids = {item.id for item in changes}
        scope_domain = None
        if scope_id is not None:
            scope_domain = self.db.scalar(
                select(AuthorizedScope.domain).where(AuthorizedScope.id == scope_id)
            )

        findings = self.db.scalars(
            select(Finding)
            .where(Finding.created_at >= cutoff)
            .order_by(Finding.created_at.desc())
            .limit(300)
        ).all()
        if scope_domain:
            normalized_scope = scope_domain.strip().lower().rstrip(".")
            findings = [
                item
                for item in findings
                if item.change_id in change_ids
                or item.asset_identifier.lower().rstrip(".") == normalized_scope
                or item.asset_identifier.lower().rstrip(".").endswith("." + normalized_scope)
            ]

        if findings:
            evidence_count = self.db.scalar(
                select(func.count(Evidence.id)).where(Evidence.finding_id.in_([item.id for item in findings]))
            ) or 0
        else:
            evidence_count = 0

        severity_counts = Counter(str(item.severity).lower() for item in findings)
        finding_type_counts = Counter(str(item.finding_type) for item in findings)
        change_type_counts = Counter(str(item.change_type) for item in changes)

        return {
            "generated_at": datetime.utcnow(),
            "period_days": days,
            "scope_id": scope_id,
            "summary": {
                "active_scopes": self.db.scalar(active_scope_query) or 0,
                "snapshots": len(snapshots),
                "changes": len(changes),
                "findings": len(findings),
                "open_findings": sum(item.status == "open" and not item.false_positive for item in findings),
                "false_positives": sum(bool(item.false_positive) for item in findings),
                "evidence_records": evidence_count,
            },
            "severity_counts": dict(severity_counts),
            "finding_type_counts": dict(finding_type_counts),
            "change_type_counts": dict(change_type_counts),
            "recent_changes": [
                {
                    "id": item.id,
                    "asset_type": item.asset_type,
                    "asset_identifier": item.asset_identifier,
                    "change_type": item.change_type,
                    "detected_at": item.detected_at,
                }
                for item in changes[:20]
            ],
            "recent_findings": [
                {
                    "id": item.id,
                    "asset_identifier": item.asset_identifier,
                    "finding_type": item.finding_type,
                    "severity": item.severity,
                    "title": item.title,
                    "status": item.status,
                    "false_positive": item.false_positive,
                    "created_at": item.created_at,
                }
                for item in findings[:20]
            ],
        }
