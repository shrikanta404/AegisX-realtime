import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.change import Change
from app.models.evidence import Evidence
from app.models.finding import Finding


class EvidenceService:
    def __init__(self, db: Session):
        self.db = db

    def create_evidence(
        self,
        finding: Finding,
        evidence_type: str,
        evidence_data: Any,
        commit: bool = True,
    ) -> Evidence:
        if not isinstance(evidence_data, str):
            evidence_data = json.dumps(evidence_data, default=str)

        evidence = Evidence(
            finding_id=finding.id,
            evidence_type=evidence_type,
            evidence_data=evidence_data,
            collected_at=datetime.utcnow(),
        )
        self.db.add(evidence)
        self.db.flush()
        if commit:
            self.db.commit()
            self.db.refresh(evidence)
        return evidence

    def create_change_evidence(self, finding: Finding, change: Change, commit: bool = False) -> Evidence:
        data = {
            "change_id": change.id,
            "change_type": change.change_type,
            "asset_type": change.asset_type,
            "asset_identifier": change.asset_identifier,
            "previous_state": change.previous_state,
            "current_state": change.current_state,
            "detected_at": change.detected_at,
            "snapshot_id": change.snapshot_id,
            "source": "change_detection",
        }
        return self.create_evidence(
            finding=finding,
            evidence_type="change_detection",
            evidence_data=data,
            commit=commit,
        )
