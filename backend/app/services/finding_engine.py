import json
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.change import Change
from app.models.finding import Finding
from app.services.evidence_service import EvidenceService


class FindingEngine:
    def __init__(self, db: Session):
        self.db = db
        self.evidence = EvidenceService(db)

    def analyze_change(self, change: Change) -> Finding | None:
        existing = self.db.scalar(select(Finding).where(Finding.change_id == change.id))
        if existing is not None:
            return existing

        finding_data = self._classify_change(change)
        if finding_data is None:
            return None

        finding = Finding(
            change_id=change.id,
            asset_identifier=change.asset_identifier,
            finding_type=finding_data["finding_type"],
            severity=finding_data["severity"],
            title=finding_data["title"],
            description=finding_data["description"],
            status="open",
            false_positive=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(finding)
        self.db.flush()
        self.evidence.create_change_evidence(finding, change, commit=False)
        self.db.commit()
        self.db.refresh(finding)
        return finding

    def analyze_changes(self, changes: list[Change]) -> list[Finding]:
        findings: list[Finding] = []
        for change in changes:
            finding = self.analyze_change(change)
            if finding is not None:
                findings.append(finding)
        return findings

    def analyze_security_issue(
        self,
        issue: dict[str, Any],
        snapshot_id: int | None = None,
    ) -> Finding | None:
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        latest = self.db.scalar(
            select(Finding)
            .where(
                Finding.finding_type == issue["finding_type"],
                Finding.asset_identifier == issue["asset_identifier"],
                Finding.created_at >= recent_cutoff,
            )
            .order_by(Finding.created_at.desc())
        )
        if latest is not None:
            return latest

        finding = Finding(
            change_id=None,
            asset_identifier=issue["asset_identifier"],
            finding_type=issue["finding_type"],
            severity=issue["severity"],
            title=issue["title"],
            description=issue["description"],
            status="open",
            false_positive=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(finding)
        self.db.flush()

        evidence_data = dict(issue.get("evidence", {}))
        evidence_data["snapshot_id"] = snapshot_id
        self.evidence.create_evidence(
            finding=finding,
            evidence_type=issue.get("evidence_type", issue["finding_type"]),
            evidence_data=evidence_data,
            commit=False,
        )

        self.db.commit()
        self.db.refresh(finding)
        return finding

    def _classify_change(self, change: Change) -> dict[str, Any] | None:
        change_type = change.change_type

        if change_type == "new_service":
            return {
                "finding_type": "unexpected_service",
                "severity": "medium",
                "title": "New exposed service detected",
                "description": (
                    f"A new service was detected at {change.asset_identifier}. "
                    "Verify that this service is authorized and expected within the approved scope."
                ),
            }

        if change_type == "service_removed":
            return {
                "finding_type": "service_removed",
                "severity": "info",
                "title": "Exposed service removed",
                "description": f"The service at {change.asset_identifier} is no longer detected.",
            }

        if change_type == "service_state_changed":
            current_state = self._json_state(change.current_state)
            previous_state = self._json_state(change.previous_state)
            if current_state.get("state") == "open" and previous_state.get("state") != "open":
                return {
                    "finding_type": "unexpected_service",
                    "severity": "medium",
                    "title": "Previously closed service is now exposed",
                    "description": (
                        f"The service at {change.asset_identifier} changed from closed to open. "
                        "Verify that the exposure is expected and authorized."
                    ),
                }
            return {
                "finding_type": "service_state_change",
                "severity": "medium",
                "title": "Service state changed",
                "description": (
                    f"The service state changed at {change.asset_identifier}. "
                    "Review whether the change was expected."
                ),
            }

        if change_type == "service_changed":
            return {
                "finding_type": "service_metadata_change",
                "severity": "low",
                "title": "Service metadata changed",
                "description": f"Service metadata changed at {change.asset_identifier}.",
            }

        if change_type == "dns_record_added":
            return {
                "finding_type": "dns_record_added",
                "severity": "low",
                "title": "DNS record added",
                "description": (
                    f"A new DNS record was detected: {change.asset_identifier}. "
                    "Verify that the record is authorized."
                ),
            }

        if change_type == "dns_record_removed":
            return {
                "finding_type": "dns_record_removed",
                "severity": "low",
                "title": "DNS record removed",
                "description": f"A DNS record was removed: {change.asset_identifier}.",
            }

        if change_type == "tls_certificate_changed":
            return {
                "finding_type": "tls_certificate_change",
                "severity": "medium",
                "title": "TLS certificate changed",
                "description": (
                    f"The TLS certificate changed for {change.asset_identifier}. "
                    "Verify the new certificate and its validity."
                ),
            }

        return None

    @staticmethod
    def _json_state(value: str | None) -> dict[str, Any]:
        if not value:
            return {}
        try:
            data = json.loads(value)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}
