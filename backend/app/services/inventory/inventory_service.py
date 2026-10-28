import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.asset import DNSRecord, Domain, Host, Service, TLSCertificate
from app.models.inventory import InventorySnapshot
from app.services.scope_guard import ScopeGuard
from app.services.inventory.dns_collector import DNSCollector
from app.services.inventory.service_collector import ServiceCollector
from app.services.inventory.tls_collector import TLSCollector


class InventoryService:
    def __init__(self, db: Session):
        self.db = db
        self.scope_guard = ScopeGuard(db)
        self.dns_collector = DNSCollector()
        self.tls_collector = TLSCollector()
        self.service_collector = ServiceCollector()

    def run_domain_inventory(self, domain: str) -> InventorySnapshot:
        scope = self.scope_guard.validate_domain(domain)
        normalized_domain = self.scope_guard.normalize_domain(domain)
        now = datetime.utcnow()
        checks = self.scope_guard.allowed_checks(scope)
        ports = self.scope_guard.allowed_ports(scope)

        try:
            domain_asset = (
                self.db.query(Domain)
                .filter(Domain.scope_id == scope.id, Domain.name == normalized_domain)
                .first()
            )
            if domain_asset is None:
                domain_asset = Domain(
                    scope_id=scope.id,
                    name=normalized_domain,
                    status="active",
                    discovered_at=now,
                    last_seen_at=now,
                )
                self.db.add(domain_asset)
                self.db.flush()
            else:
                domain_asset.status = "active"
                domain_asset.last_seen_at = now

            host = (
                self.db.query(Host)
                .filter(Host.scope_id == scope.id, Host.hostname == normalized_domain)
                .first()
            )
            if host is None:
                host_count = self.db.query(Host).filter(Host.scope_id == scope.id).count()
                self.scope_guard.validate_host_limit(scope, normalized_domain, host_count)

            snapshot = InventorySnapshot(
                scope_id=scope.id,
                snapshot_type="domain",
                status="running",
                started_at=now,
            )
            self.db.add(snapshot)
            self.db.flush()

            dns_records: list[dict] = self.dns_collector.collect(normalized_domain) if "dns" in checks else []
            ip_address = next(
                (record["value"] for record in dns_records if record["record_type"] == "A"),
                None,
            )
            if ip_address is None:
                ip_address = next(
                    (record["value"] for record in dns_records if record["record_type"] == "AAAA"),
                    None,
                )

            for record in dns_records:
                existing = (
                    self.db.query(DNSRecord)
                    .filter(
                        DNSRecord.domain_id == domain_asset.id,
                        DNSRecord.record_type == record["record_type"],
                        DNSRecord.name == record["name"],
                        DNSRecord.value == record["value"],
                    )
                    .first()
                )
                if existing is None:
                    existing = DNSRecord(
                        domain_id=domain_asset.id,
                        record_type=record["record_type"],
                        name=record["name"],
                        value=record["value"],
                        ttl=record.get("ttl"),
                        last_seen_at=now,
                    )
                    self.db.add(existing)
                else:
                    existing.ttl = record.get("ttl")
                    existing.last_seen_at = now

            tls_certificate: dict = {"error": "TLS check not enabled for this scope."}
            if "tls" in checks:
                try:
                    tls_certificate = self.tls_collector.collect(normalized_domain)
                except Exception as exc:
                    tls_certificate = {"error": str(exc), "domain": normalized_domain}

            if tls_certificate and "error" not in tls_certificate:
                certificate = (
                    self.db.query(TLSCertificate)
                    .filter(TLSCertificate.domain_id == domain_asset.id)
                    .first()
                )
                if certificate is None:
                    certificate = TLSCertificate(domain_id=domain_asset.id)
                    self.db.add(certificate)
                certificate.subject = tls_certificate.get("subject")
                certificate.issuer = tls_certificate.get("issuer")
                certificate.serial_number = tls_certificate.get("serial_number")
                certificate.valid_from = self._to_naive_datetime(tls_certificate.get("valid_from"))
                certificate.valid_until = self._to_naive_datetime(tls_certificate.get("valid_until"))
                certificate.fingerprint = tls_certificate.get("fingerprint")
                certificate.is_expired = bool(tls_certificate.get("is_expired"))
                certificate.last_checked_at = now

            service_results: list[dict] = []
            if "service" in checks:
                service_results = self.service_collector.collect(normalized_domain, ports)

            if host is None:
                host = Host(
                    scope_id=scope.id,
                    hostname=normalized_domain,
                    ip_address=ip_address,
                    status="active",
                    discovered_at=now,
                    last_seen_at=now,
                )
                self.db.add(host)
                self.db.flush()
            else:
                host.ip_address = ip_address or host.ip_address
                host.status = "active"
                host.last_seen_at = now

            for result in service_results:
                service = (
                    self.db.query(Service)
                    .filter(
                        Service.host_id == host.id,
                        Service.port == result["port"],
                        Service.protocol == result["protocol"],
                    )
                    .first()
                )
                if service is None:
                    service = Service(
                        host_id=host.id,
                        port=result["port"],
                        protocol=result["protocol"],
                    )
                    self.db.add(service)
                service.service_name = result.get("service_name")
                service.version = result.get("version")
                service.state = result["state"]
                service.last_seen_at = now

            snapshot.inventory_json = json.dumps(
                {
                    "domain": normalized_domain,
                    "scope_id": scope.id,
                    "ip_address": ip_address,
                    "checks": sorted(checks),
                    "allowed_ports": ports,
                    "dns_records": dns_records,
                    "tls_certificate": tls_certificate,
                    "services": service_results,
                    "collected_at": now.isoformat(),
                },
                default=str,
            )
            snapshot.status = "completed"
            snapshot.completed_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(snapshot)
            return snapshot

        except Exception as exc:
            self.db.rollback()
            failed = InventorySnapshot(
                scope_id=scope.id,
                snapshot_type="domain",
                status="failed",
                inventory_json=json.dumps(
                    {"domain": normalized_domain, "error": str(exc)},
                    default=str,
                ),
                started_at=now,
                completed_at=datetime.utcnow(),
            )
            self.db.add(failed)
            self.db.commit()
            raise

    @staticmethod
    def _to_naive_datetime(value):
        if value is None:
            return None
        if hasattr(value, "tzinfo") and value.tzinfo is not None:
            return value.replace(tzinfo=None)
        return value
