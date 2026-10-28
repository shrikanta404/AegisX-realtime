import ast
import json
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.change import Change
from app.models.inventory import InventorySnapshot
from app.services.change_detector import ChangeDetector


class ChangeDetectionService:
    def __init__(self, db: Session):
        self.db = db
        self.detector = ChangeDetector()

    @staticmethod
    def parse_inventory(snapshot: InventorySnapshot) -> dict[str, Any]:
        if not snapshot.inventory_json:
            return {}
        try:
            parsed = json.loads(snapshot.inventory_json)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            try:
                parsed = ast.literal_eval(snapshot.inventory_json)
                return parsed if isinstance(parsed, dict) else {}
            except (ValueError, SyntaxError):
                return {}

    def get_domain_snapshots(self, scope_id: int, domain: str) -> list[InventorySnapshot]:
        normalized = domain.strip().lower().rstrip(".")
        snapshots = self.db.scalars(
            select(InventorySnapshot)
            .where(
                InventorySnapshot.scope_id == scope_id,
                InventorySnapshot.status == "completed",
            )
            .order_by(InventorySnapshot.id.desc())
        ).all()
        matching: list[InventorySnapshot] = []
        for snapshot in snapshots:
            snapshot_domain = str(self.parse_inventory(snapshot).get("domain", "")).strip().lower().rstrip(".")
            if snapshot_domain == normalized:
                matching.append(snapshot)
        return matching

    def create_change(self, snapshot_id: int, detected: dict[str, Any]) -> Change:
        change = Change(
            snapshot_id=snapshot_id,
            asset_type=detected["asset_type"],
            asset_identifier=detected["asset_identifier"],
            change_type=detected["change_type"],
            previous_state=(
                json.dumps(detected["previous_state"], default=str)
                if detected.get("previous_state") is not None else None
            ),
            current_state=(
                json.dumps(detected["current_state"], default=str)
                if detected.get("current_state") is not None else None
            ),
            detected_at=datetime.utcnow(),
        )
        self.db.add(change)
        return change

    def detect_service_changes(self, previous_snapshot: InventorySnapshot, current_snapshot: InventorySnapshot) -> list[dict[str, Any]]:
        previous = self.parse_inventory(previous_snapshot).get("services", [])
        current = self.parse_inventory(current_snapshot).get("services", [])
        return self.detector.compare_services(previous, current)

    def detect_dns_changes(self, previous_snapshot: InventorySnapshot, current_snapshot: InventorySnapshot) -> list[dict[str, Any]]:
        previous = self.parse_inventory(previous_snapshot).get("dns_records", [])
        current = self.parse_inventory(current_snapshot).get("dns_records", [])
        return self.detector.compare_dns(previous, current)

    def detect_tls_changes(self, previous_snapshot: InventorySnapshot, current_snapshot: InventorySnapshot) -> list[dict[str, Any]]:
        previous = self.parse_inventory(previous_snapshot).get("tls_certificate")
        current = self.parse_inventory(current_snapshot).get("tls_certificate")
        return self.detector.compare_tls(previous, current)

    def detect_all_changes(self, previous_snapshot: InventorySnapshot, current_snapshot: InventorySnapshot) -> list[dict[str, Any]]:
        changes: list[dict[str, Any]] = []
        changes.extend(self.detect_service_changes(previous_snapshot, current_snapshot))
        changes.extend(self.detect_dns_changes(previous_snapshot, current_snapshot))
        changes.extend(self.detect_tls_changes(previous_snapshot, current_snapshot))
        return changes

    def compare_domain(self, scope_id: int, domain: str) -> dict[str, Any]:
        normalized = domain.strip().lower().rstrip(".")
        snapshots = self.get_domain_snapshots(scope_id, normalized)

        if not snapshots:
            return {
                "status": "no_inventory",
                "domain": normalized,
                "message": f"No completed inventory found for '{normalized}'.",
                "changes": [],
            }

        current = snapshots[0]
        if len(snapshots) == 1:
            return {
                "status": "baseline_created",
                "domain": normalized,
                "current_snapshot_id": current.id,
                "change_count": 0,
                "changes": [],
            }

        previous = snapshots[1]
        detected = self.detect_all_changes(previous, current)

        existing_current = self.db.scalars(
            select(Change).where(Change.snapshot_id == current.id)
        ).all()
        existing_signatures = {
            (item.asset_type, item.asset_identifier, item.change_type)
            for item in existing_current
        }

        records: list[Change] = []
        for item in detected:
            signature = (
                item["asset_type"],
                item["asset_identifier"],
                item["change_type"],
            )
            if signature in existing_signatures:
                continue
            records.append(self.create_change(current.id, item))
            existing_signatures.add(signature)

        if records:
            self.db.commit()
            for item in records:
                self.db.refresh(item)

        return {
            "status": "completed",
            "domain": normalized,
            "previous_snapshot_id": previous.id,
            "current_snapshot_id": current.id,
            "change_count": len(records),
            "changes": [
                {
                    "id": item.id,
                    "asset_type": item.asset_type,
                    "asset_identifier": item.asset_identifier,
                    "change_type": item.change_type,
                    "previous_state": item.previous_state,
                    "current_state": item.current_state,
                    "detected_at": item.detected_at,
                }
                for item in records
            ],
        }

    def list_changes(
        self,
        scope_id: int | None = None,
        domain: str | None = None,
        limit: int = 100,
    ) -> list[Change]:
        query = select(Change).order_by(Change.detected_at.desc()).limit(limit)
        if scope_id is not None:
            query = query.join(InventorySnapshot, Change.snapshot_id == InventorySnapshot.id).where(
                InventorySnapshot.scope_id == scope_id
            )
        rows = self.db.scalars(query).all()
        if not domain:
            return rows
        normalized = domain.strip().lower().rstrip(".")
        return [row for row in rows if normalized in (row.asset_identifier or "").lower()]
