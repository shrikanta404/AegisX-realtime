import json
from sqlalchemy.orm import Session

from app.models.evidence import Evidence
from app.models.finding import Finding
from app.services.ai.gemini_service import GeminiService
from app.services.threat_intelligence.abuseipdb_service import AbuseIPDBService
from app.services.threat_intelligence.virustotal_service import VirusTotalService


class UnifiedAnalysisService:
    def __init__(self, db: Session):
        self.db = db

    def analyze_finding(self, finding_id: int) -> dict:
        finding = self.db.query(Finding).filter(Finding.id == finding_id).first()
        if finding is None:
            raise ValueError(f"Finding {finding_id} was not found.")

        evidence = self.db.query(Evidence).filter(Evidence.finding_id == finding.id).order_by(Evidence.collected_at.desc()).all()
        finding_data = {
            "id": finding.id,
            "asset_identifier": finding.asset_identifier,
            "finding_type": finding.finding_type,
            "severity": finding.severity,
            "title": finding.title,
            "description": finding.description,
            "status": finding.status,
            "false_positive": finding.false_positive,
            "evidence": [
                {
                    "id": item.id,
                    "type": item.evidence_type,
                    "data": item.evidence_data,
                    "collected_at": item.collected_at,
                }
                for item in evidence
            ],
        }

        asset = self._extract_asset(finding.asset_identifier)
        virustotal_result = None
        abuseipdb_result = None
        if asset["type"] == "domain":
            virustotal_result = VirusTotalService().lookup_domain(asset["value"])
        elif asset["type"] == "ip":
            abuseipdb_result = AbuseIPDBService().check_ip(asset["value"])

        input_data = {
            "finding": finding_data,
            "threat_intelligence": {
                "virustotal": virustotal_result,
                "abuseipdb": abuseipdb_result,
            },
        }

        try:
            ai_analysis = GeminiService().analyze_finding(input_data)
            ai_status = "success"
        except Exception as exc:
            ai_analysis = (
                "Gemini analysis is unavailable. Use the deterministic finding and evidence above. "
                f"Reason: {exc}"
            )
            ai_status = "unavailable"

        return {
            "finding_id": finding.id,
            "finding": finding_data,
            "threat_intelligence": {
                "virustotal": virustotal_result,
                "abuseipdb": abuseipdb_result,
            },
            "ai_status": ai_status,
            "ai_analysis": ai_analysis,
        }

    @staticmethod
    def _extract_asset(asset_identifier: str | None) -> dict:
        if not asset_identifier:
            return {"type": "unknown", "value": None}

        value = asset_identifier.strip()
        if ":" in value:
            possible_host, possible_port = value.rsplit(":", 1)
            if possible_port.isdigit():
                value = possible_host

        parts = value.split(".")
        if len(parts) == 4 and all(part.isdigit() for part in parts):
            return {"type": "ip", "value": value}
        if "." in value:
            return {"type": "domain", "value": value}
        return {"type": "unknown", "value": value}
