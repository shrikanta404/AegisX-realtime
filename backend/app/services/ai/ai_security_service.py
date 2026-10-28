from typing import Any


class AISecurityService:
    """Deterministic fallback/security-safe analyst utilities."""

    def explain_finding(self, finding: dict[str, Any]) -> dict[str, Any]:
        severity = finding.get("severity", "unknown")
        title = finding.get("title", "Security finding")
        asset = finding.get("asset_identifier", "unknown asset")
        description = finding.get("description") or ""
        return {
            "asset": asset,
            "severity": severity,
            "explanation": f"{title} was detected on {asset}. The recorded severity is {severity}. {description}",
            "recommended_review": "Verify that the observation is authorized and expected within the approved monitoring scope.",
        }

    def summarize_findings(self, findings: list[dict[str, Any]]) -> dict[str, Any]:
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for finding in findings:
            severity = str(finding.get("severity", "info")).lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        return {
            "total_findings": len(findings),
            "severity_counts": severity_counts,
            "summary": (
                f"AegisX currently has {len(findings)} recorded findings. "
                f"{severity_counts['critical']} critical, {severity_counts['high']} high, "
                f"{severity_counts['medium']} medium, {severity_counts['low']} low, "
                f"and {severity_counts['info']} informational."
            ),
        }

    def correlate_changes(self, changes: list[dict[str, Any]]) -> dict[str, Any]:
        if not changes:
            return {"change_count": 0, "correlation": "No changes were supplied for analysis."}
        return {
            "change_count": len(changes),
            "correlation": (
                "Review the supplied changes together to determine whether they correspond to an expected deployment, "
                "configuration change, or an unexpected attack-surface change."
            ),
        }
