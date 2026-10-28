import httpx

from app.core.config import settings


class AbuseIPDBService:
    BASE_URL = "https://api.abuseipdb.com/api/v2/check"

    def check_ip(self, ip_address: str) -> dict:
        if not settings.abuseipdb_api_key:
            return {"status": "disabled", "reason": "AbuseIPDB API key is not configured."}
        try:
            response = httpx.get(
                self.BASE_URL,
                headers={
                    "Key": settings.abuseipdb_api_key,
                    "Accept": "application/json",
                },
                params={"ipAddress": ip_address, "maxAgeInDays": 90},
                timeout=15,
            )
        except httpx.HTTPError as exc:
            return {"status": "error", "message": str(exc)}

        if response.status_code != 200:
            return {"status": "error", "http_status": response.status_code}

        data = response.json().get("data", {})
        return {
            "status": "success",
            "ip_address": ip_address,
            "abuse_confidence_score": data.get("abuseConfidenceScore"),
            "total_reports": data.get("totalReports"),
            "country_code": data.get("countryCode"),
            "isp": data.get("isp"),
        }
