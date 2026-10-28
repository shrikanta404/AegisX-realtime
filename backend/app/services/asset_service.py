from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import DNSRecord, Domain, Host, Service, TLSCertificate
from app.models.inventory import InventorySnapshot
from app.models.scope import AuthorizedScope


class AssetService:
    def __init__(self, db: Session):
        self.db = db

    def list_assets(self, scope_id: int | None = None, search: str | None = None) -> list[dict[str, Any]]:
        domain_query = select(Domain).order_by(Domain.last_seen_at.desc())
        host_query = select(Host).order_by(Host.last_seen_at.desc())
        service_query = select(Service).order_by(Service.last_seen_at.desc())
        tls_query = select(TLSCertificate).order_by(TLSCertificate.last_checked_at.desc())

        if scope_id is not None:
            domain_query = domain_query.where(Domain.scope_id == scope_id)
            host_query = host_query.where(Host.scope_id == scope_id)
            service_query = service_query.join(Host, Service.host_id == Host.id).where(Host.scope_id == scope_id)
            tls_query = tls_query.join(Domain, TLSCertificate.domain_id == Domain.id).where(Domain.scope_id == scope_id)

        domains = self.db.scalars(domain_query).all()
        hosts = self.db.scalars(host_query).all()
        services = self.db.scalars(service_query).all()
        tls_rows = self.db.scalars(tls_query).all()

        scope_ids = {item.scope_id for item in domains}
        if scope_id is not None:
            scope_ids.add(scope_id)
        dns_rows = self._current_dns_rows(scope_id)

        domain_names = {item.id: item.name for item in domains}
        host_map = {item.id: item for item in hosts}
        results: list[dict[str, Any]] = []

        for item in domains:
            results.append({
                "id": f"domain-{item.id}",
                "type": "Domain",
                "name": item.name,
                "address": item.name,
                "status": "Normal" if item.status == "active" else item.status.title(),
                "last_seen": item.last_seen_at,
                "details": f"Authorized scope asset #{item.scope_id}",
                "scope_id": item.scope_id,
            })

        for item in hosts:
            results.append({
                "id": f"host-{item.id}",
                "type": "Host",
                "name": item.hostname or item.ip_address or f"host-{item.id}",
                "address": item.ip_address or "unresolved",
                "status": "Normal" if item.status == "active" else item.status.title(),
                "last_seen": item.last_seen_at,
                "details": f"Host under authorized scope #{item.scope_id}",
                "scope_id": item.scope_id,
            })

        for item in services:
            host = host_map.get(item.host_id)
            if host is None:
                continue
            status = "Normal" if item.state == "open" else "Changed"
            results.append({
                "id": f"service-{item.id}",
                "type": "Service",
                "name": f"{item.service_name or 'tcp'} :{item.port}",
                "address": f"{host.hostname or host.ip_address or 'host'}:{item.port}",
                "status": status,
                "last_seen": item.last_seen_at,
                "details": f"{item.protocol.upper()} service is {item.state}",
                "scope_id": host.scope_id,
            })

        for item in dns_rows:
            scope_value = self.db.scalar(
                select(Domain.scope_id).where(Domain.id == item.domain_id)
            )
            if scope_value is None:
                continue
            results.append({
                "id": f"dns-{item.id}",
                "type": "DNS",
                "name": item.name,
                "address": item.value,
                "status": "Normal",
                "last_seen": item.last_seen_at,
                "details": f"{item.record_type} record",
                "scope_id": scope_value,
            })

        for item in tls_rows:
            domain = self.db.scalar(select(Domain).where(Domain.id == item.domain_id))
            if domain is None:
                continue
            status = "Warning" if item.is_expired else "Normal"
            results.append({
                "id": f"tls-{item.id}",
                "type": "TLS",
                "name": "TLS Certificate",
                "address": domain.name,
                "status": status,
                "last_seen": item.last_checked_at,
                "details": (
                    f"Expired {item.valid_until.isoformat()}" if item.is_expired and item.valid_until
                    else f"Valid until {item.valid_until.isoformat()}" if item.valid_until
                    else "Certificate metadata collected"
                ),
                "scope_id": domain.scope_id,
            })

        if scope_ids:
            results = [item for item in results if item.get("scope_id") in scope_ids]

        if search:
            query = search.strip().lower()
            results = [
                item for item in results
                if query in str(item.get("name", "")).lower()
                or query in str(item.get("address", "")).lower()
                or query in str(item.get("details", "")).lower()
            ]

        return results

    def summary(self, scope_id: int | None = None) -> dict[str, int]:
        assets = self.list_assets(scope_id=scope_id)
        return {
            "domains": sum(item["type"] == "Domain" for item in assets),
            "hosts": sum(item["type"] == "Host" for item in assets),
            "services": sum(item["type"] == "Service" for item in assets),
            "dns_records": sum(item["type"] == "DNS" for item in assets),
            "tls_certificates": sum(item["type"] == "TLS" for item in assets),
        }

    def _current_dns_rows(self, scope_id: int | None) -> list[DNSRecord]:
        query = select(DNSRecord).order_by(DNSRecord.last_seen_at.desc())
        if scope_id is not None:
            query = query.join(Domain, DNSRecord.domain_id == Domain.id).where(Domain.scope_id == scope_id)

        rows = self.db.scalars(query).all()
        # Keep only the latest observation for each domain/type/name/value tuple.
        seen: set[tuple[int, str, str, str]] = set()
        current: list[DNSRecord] = []
        for row in rows:
            key = (row.domain_id, row.record_type, row.name, row.value)
            if key in seen:
                continue
            seen.add(key)
            current.append(row)
        return current
