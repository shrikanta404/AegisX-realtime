import socket
from typing import Any


class ServiceCollector:
    SERVICE_NAMES = {
        22: "ssh",
        25: "smtp",
        53: "dns",
        80: "http",
        110: "pop3",
        143: "imap",
        443: "https",
        445: "smb",
        3306: "mysql",
        5432: "postgresql",
        6379: "redis",
        8080: "http-alt",
    }

    def collect(self, host: str, ports: list[int], timeout: float = 2.0) -> list[dict[str, Any]]:
        host = host.strip()
        results: list[dict[str, Any]] = []

        for port in sorted(set(ports)):
            result: dict[str, Any] = {
                "host": host,
                "port": port,
                "protocol": "tcp",
                "state": "closed",
                "service_name": self.SERVICE_NAMES.get(port),
                "version": None,
            }
            try:
                with socket.create_connection((host, port), timeout=timeout):
                    result["state"] = "open"
                    if result["service_name"] is None:
                        try:
                            result["service_name"] = socket.getservbyport(port, "tcp")
                        except OSError:
                            result["service_name"] = "unknown"
            except (TimeoutError, OSError, socket.timeout):
                pass
            results.append(result)

        return results
