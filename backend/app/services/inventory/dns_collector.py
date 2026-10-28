from typing import Any

import dns.exception
import dns.resolver


class DNSCollector:
    """
    Collect current DNS records through the configured DNS resolver.

    No brute-force discovery is performed. Only the supplied authorized
    hostname is queried.
    """

    RECORD_TYPES = ("A", "AAAA", "CNAME", "MX", "NS", "TXT")

    def __init__(self) -> None:
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = 3.0
        self.resolver.lifetime = 5.0

    def collect(self, domain: str) -> list[dict[str, Any]]:
        domain = domain.strip().lower().rstrip(".")
        records: list[dict[str, Any]] = []

        for record_type in self.RECORD_TYPES:
            try:
                answers = self.resolver.resolve(domain, record_type, raise_on_no_answer=False)
            except (dns.exception.DNSException, OSError):
                continue

            if not answers:
                continue

            ttl = answers.rrset.ttl if answers.rrset is not None else None
            for answer in answers:
                value = self._answer_to_value(answer, record_type)
                if value is None:
                    continue
                records.append(
                    {
                        "record_type": record_type,
                        "name": domain,
                        "value": value,
                        "ttl": ttl,
                    }
                )

        return self._deduplicate(records)

    @staticmethod
    def _answer_to_value(answer: Any, record_type: str) -> str | None:
        if record_type in {"A", "AAAA", "CNAME", "NS"}:
            return str(answer).rstrip(".")
        if record_type == "MX":
            exchange = getattr(answer, "exchange", None)
            preference = getattr(answer, "preference", None)
            if exchange is None:
                return str(answer).rstrip(".")
            return f"{preference} {exchange}".strip().rstrip(".")
        if record_type == "TXT":
            strings = getattr(answer, "strings", None)
            if strings:
                return "".join(
                    part.decode("utf-8", errors="replace") if isinstance(part, bytes) else str(part)
                    for part in strings
                )
            return str(answer).strip('"')
        return str(answer)

    @staticmethod
    def _deduplicate(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[tuple[str, str, str]] = set()
        unique: list[dict[str, Any]] = []
        for record in records:
            key = (
                record["record_type"],
                record["name"],
                record["value"],
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(record)
        return unique
