from datetime import datetime, timedelta, timezone

from app.services.change_detector import ChangeDetector
from app.services.security_issue_detector import SecurityIssueDetector


def main() -> None:
    detector = ChangeDetector()
    changes = detector.compare_services(
        [{"host": "authorized-lab.example", "port": 443, "protocol": "tcp", "state": "closed", "service_name": "https", "version": None}],
        [{"host": "authorized-lab.example", "port": 443, "protocol": "tcp", "state": "open", "service_name": "https", "version": None}],
    )
    assert changes[0]["change_type"] == "service_state_changed"

    tls = SecurityIssueDetector().detect_expired_tls(
        "authorized-lab.example",
        {
            "valid_from": datetime.now(timezone.utc) - timedelta(days=400),
            "valid_until": datetime.now(timezone.utc) - timedelta(days=1),
            "subject": "CN=authorized-lab.example",
            "issuer": "Test CA",
            "is_expired": True,
        },
    )
    assert tls is not None
    assert tls["finding_type"] == "expired_tls_certificate"

    valid_tls = SecurityIssueDetector().detect_expired_tls(
        "authorized-lab.example",
        {"valid_until": datetime.now(timezone.utc) + timedelta(days=30)},
    )
    assert valid_tls is None

    print("AegisX offline core tests: OK")


if __name__ == "__main__":
    main()
