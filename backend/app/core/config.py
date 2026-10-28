from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AegisX"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://aegisx_user:CHANGE_ME@localhost:5432/aegisx_dev"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"
    virustotal_api_key: str | None = None
    abuseipdb_api_key: str | None = None

    cors_origins: str = "http://localhost:5173"

    # Live monitoring. The scheduler runs only against active authorized scopes.
    scheduler_enabled: bool = True
    scheduler_interval_seconds: int | None = None
    # Backward compatibility with older .env files.
    scheduler_interval_minutes: int = 30

    max_authorized_domains: int = 20
    max_hosts_per_scope: int = 10
    default_ports: str = "80,443,22,8080"
    default_checks: str = "dns,tls,service"

    # Frontend refresh cadence. This only refreshes API data; it does not scan by itself.
    ui_refresh_seconds: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            item.strip()
            for item in self.cors_origins.split(",")
            if item.strip()
        ]

    @property
    def default_port_list(self) -> list[int]:
        ports: list[int] = []
        for raw in self.default_ports.split(","):
            raw = raw.strip()
            if not raw:
                continue
            try:
                port = int(raw)
            except ValueError:
                continue
            if 1 <= port <= 65535:
                ports.append(port)
        return sorted(set(ports))

    @property
    def default_check_list(self) -> list[str]:
        return [
            item.strip().lower()
            for item in self.default_checks.split(",")
            if item.strip()
        ]

    @property
    def effective_scheduler_interval_seconds(self) -> int:
        # Prefer the new seconds setting, but allow old .env files to keep working.
        configured = self.scheduler_interval_seconds
        if configured is None:
            configured = self.scheduler_interval_minutes * 60
        return max(30, configured)

    @property
    def effective_ui_refresh_seconds(self) -> int:
        return max(2, self.ui_refresh_seconds)


settings = Settings()
