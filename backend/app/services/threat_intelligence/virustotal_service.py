import httpx

from app.core.config import settings


class VirusTotalService:
    BASE_URL = "https://www.virustotal.com/api/v3"

    def lookup_domain(self, domain: str) -> dict:
        if not settings.virustotal_api_key:
            return {"status": "disabled", "reason": "VirusTotal API key is not configured."}
        try:
            response = httpx.get(
                f"{self.BASE_URL}/domains/{domain}",
                headers={"x-apikey": settings.virustotal_api_key},
                timeout=15,
            )
        except httpx.HTTPError as exc:
            return {"status": "error", "message": str(exc)}

        if response.status_code != 200:
            return {"status": "error", "http_status": response.status_code}

        attributes = response.json().get("data", {}).get("attributes", {})
        return {
            "status": "success",
            "domain": domain,
            "reputation": attributes.get("reputation"),
            "last_analysis_stats": attributes.get("last_analysis_stats"),
        }
