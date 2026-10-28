import socket
from datetime import datetime, timezone
from typing import Any


class SecurityIssueDetector:
    """Deterministic checks over already-collected authorized inventory data."""

    def detect_expired_tls(self, domain: str, tls_data: dict[str, Any] | None) -> dict[str, Any] | None:
        if not tls_data or "error" in tls_data:
            return None

        valid_until = tls_data.get("valid_until")
        if valid_until is None:
            return None

        if isinstance(valid_until, str):
            try:
                valid_until = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
            except ValueError:
                return None

        if not isinstance(valid_until, datetime):
            return None
        if valid_until.tzinfo is None:
            valid_until = valid_until.replace(tzinfo=timezone.utc)

        if valid_until >= datetime.now(timezone.utc):
            return None

        return {
            "finding_type": "expired_tls_certificate",
            "severity": "high",
            "title": "Expired TLS certificate detected",
            "description": (
                f"The TLS certificate for {domain} expired on {valid_until.isoformat()}. "
                "Verify the certificate configuration and replace it if it is no longer valid."
            ),
            "asset_identifier": domain,
            "evidence": {
                "domain": domain,
                "subject": tls_data.get("subject"),
                "issuer": tls_data.get("issuer"),
                "serial_number": tls_data.get("serial_number"),
                "valid_from": tls_data.get("valid_from"),
                "valid_until": valid_until,
                "fingerprint": tls_data.get("fingerprint"),
                "is_expired": True,
                "source": "tls_inventory",
            },
        }

    def detect_potential_dangling_dns(self, domain: str, dns_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        for record in dns_records:
            if str(record.get("record_type", "")).upper() != "CNAME":
                continue
            target = str(record.get("value", "")).strip().rstrip(".")
            if not target:
                continue
            try:
                socket.getaddrinfo(target, None, type=socket.SOCK_STREAM)
            except socket.gaierror:
                findings.append({
                    "finding_type": "potential_dangling_dns",
                    "severity": "medium",
                    "title": "Potential dangling DNS record detected",
                    "description": (
                        f"The CNAME target '{target}' for '{domain}' could not be resolved during the inventory check. "
                        "This is a review signal only and does not establish exploitability."
                    ),
                    "asset_identifier": domain,
                    "evidence": {
                        "domain": domain,
                        "record": record,
                        "resolution_status": "target_not_resolvable",
                        "source": "dns_inventory",
                    },
                })
        return findings
