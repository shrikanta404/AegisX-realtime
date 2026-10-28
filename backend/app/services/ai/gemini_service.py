from typing import Any

from google import genai

from app.core.config import settings


class GeminiService:
    def __init__(self):
        if not settings.gemini_api_key:
            raise RuntimeError("Gemini API key is not configured.")
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def analyze_finding(self, finding: dict[str, Any]) -> str:
        prompt = f"""
You are the AegisX Security Analyst.

Analyze only the verified information supplied below.

Rules:
- Do not invent vulnerabilities or CVEs.
- Do not claim exploitation is possible.
- Do not recommend attacking the target.
- Explain what changed or what was observed.
- Explain why a reviewer should investigate it.
- Give defensive verification/remediation steps.
- Preserve uncertainty when the evidence is incomplete.

Verified finding:
{finding}
"""
        response = self.client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )
        return response.text or "No AI analysis was returned."
