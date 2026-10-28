import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.change import Change
from app.models.inventory import InventorySnapshot
from app.services.audit_service import AuditService
from app.services.change_detection_service import ChangeDetectionService
from app.services.finding_engine import FindingEngine
from app.services.inventory.inventory_service import InventoryService
from app.services.security_issue_detector import SecurityIssueDetector
from app.services.scope_guard import ScopeGuard


class MonitoringService:
    """Orchestrates one complete authorized monitoring cycle."""

    def __init__(self, db: Session):
        self.db = db
        self.scope_guard = ScopeGuard(db)
        self.inventory = InventoryService(db)
        self.change_detection = ChangeDetectionService(db)
        self.finding_engine = FindingEngine(db)
        self.security_detector = SecurityIssueDetector()

    def run(self, domain: str, actor: str = "manual") -> dict[str, Any]:
        normalized = self.scope_guard.normalize_domain(domain)
        scope = self.scope_guard.validate_domain(normalized)

        AuditService(self.db).log(
            action="monitoring_started",
            target=normalized,
            actor=actor,
            details={"scope_id": scope.id},
        )

        snapshot = self.inventory.run_domain_inventory(normalized)
        change_result = self.change_detection.compare_domain(scope.id, normalized)

        change_ids = [item["id"] for item in change_result.get("changes", []) if item.get("id") is not None]
        changes = []
        if change_ids:
            changes = self.db.scalars(select(Change).where(Change.id.in_(change_ids))).all()

        created_findings = self.finding_engine.analyze_changes(changes)

        inventory = self._load_inventory(snapshot)
        security_issues: list[dict[str, Any]] = []
        enabled_checks = set(inventory.get("checks", []))
        if "tls" in enabled_checks:
            tls_issue = self.security_detector.detect_expired_tls(
                normalized,
                inventory.get("tls_certificate"),
            )
            if tls_issue:
                tls_issue["evidence_type"] = "tls_certificate"
                security_issues.append(tls_issue)

        if "dns" in enabled_checks:
            dns_issues = self.security_detector.detect_potential_dangling_dns(
                normalized,
                inventory.get("dns_records", []),
            )
            for issue in dns_issues:
                issue["evidence_type"] = "dns_check"
            security_issues.extend(dns_issues)

        security_findings = []
        for issue in security_issues:
            finding = self.finding_engine.analyze_security_issue(issue, snapshot.id)
            if finding is not None:
                security_findings.append(finding)

        all_findings = []
        seen_ids: set[int] = set()
        for finding in [*created_findings, *security_findings]:
            if finding.id in seen_ids:
                continue
            seen_ids.add(finding.id)
            all_findings.append(finding)

        AuditService(self.db).log(
            action="monitoring_completed",
            target=normalized,
            actor=actor,
            details={
                "scope_id": scope.id,
                "snapshot_id": snapshot.id,
                "change_count": len(change_result.get("changes", [])),
                "finding_count": len(all_findings),
            },
        )

        open_services = [
            service
            for service in inventory.get("services", [])
            if str(service.get("state", "")).lower() == "open"
        ]

        return {
            "status": "completed",
            "domain": normalized,
            "scope_id": scope.id,
            "snapshot_id": snapshot.id,
            "collected_at": inventory.get("collected_at"),
            "live_inventory": {
                "ip_address": inventory.get("ip_address"),
                "dns_records": inventory.get("dns_records", []),
                "tls_certificate": inventory.get("tls_certificate"),
                "services": inventory.get("services", []),
                "open_service_count": len(open_services),
            },
            "change_detection": change_result,
            "findings_created": [
                {
                    "id": finding.id,
                    "finding_type": finding.finding_type,
                    "severity": finding.severity,
                    "title": finding.title,
                    "asset_identifier": finding.asset_identifier,
                }
                for finding in all_findings
            ],
        }

    @staticmethod
    def _load_inventory(snapshot: InventorySnapshot) -> dict[str, Any]:
        if not snapshot.inventory_json:
            return {}
        try:
            parsed = json.loads(snapshot.inventory_json)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
