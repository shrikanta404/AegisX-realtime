from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.scope import AuthorizedScope


class ScopeGuard:
    """Authorisation boundary for every inventory operation."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def normalize_domain(domain: str) -> str:
        return domain.strip().lower().rstrip(".")

    def get_scope_for_domain(self, domain: str) -> AuthorizedScope | None:
        normalized_domain = self.normalize_domain(domain)
        scopes = self.db.scalars(
            select(AuthorizedScope).where(AuthorizedScope.is_active.is_(True))
        ).all()

        best_match: AuthorizedScope | None = None
        best_length = -1

        for scope in scopes:
            scope_domain = self.normalize_domain(scope.domain)
            if normalized_domain == scope_domain or normalized_domain.endswith("." + scope_domain):
                if len(scope_domain) > best_length:
                    best_match = scope
                    best_length = len(scope_domain)

        return best_match

    def is_authorized_domain(self, domain: str) -> bool:
        return self.get_scope_for_domain(domain) is not None

    def validate_domain(self, domain: str) -> AuthorizedScope:
        scope = self.get_scope_for_domain(domain)
        if scope is None:
            raise PermissionError(
                f"Target '{domain}' is not covered by an active authorized scope."
            )
        return scope

    def allowed_ports(self, scope: AuthorizedScope) -> list[int]:
        values = (scope.allowed_ports or "").strip()
        if not values:
            return settings.default_port_list
        ports: list[int] = []
        for raw in values.split(","):
            raw = raw.strip()
            if not raw:
                continue
            try:
                port = int(raw)
            except ValueError:
                continue
            if 1 <= port <= 65535:
                ports.append(port)
        return sorted(set(ports)) or settings.default_port_list

    def allowed_checks(self, scope: AuthorizedScope) -> set[str]:
        values = (scope.allowed_checks or "").strip()
        if not values:
            return set(settings.default_check_list)
        checks: set[str] = set()
        for raw in values.replace(";", ",").split(","):
            value = raw.strip().lower()
            if value:
                checks.add(value)
        return checks or set(settings.default_check_list)

    def validate_host_limit(self, scope: AuthorizedScope, hostname: str, current_count: int) -> None:
        if current_count >= settings.max_hosts_per_scope:
            raise PermissionError(
                f"The authorized host limit of {settings.max_hosts_per_scope} "
                f"has been reached for scope '{scope.domain}'."
            )
