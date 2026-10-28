from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.ai.unified_analysis_service import UnifiedAnalysisService


router = APIRouter(prefix="/ai-analysis", tags=["AI Security Analysis"])


@router.get("/{finding_id}")
def analyze_finding(finding_id: int, db: Session = Depends(get_db)):
    try:
        return UnifiedAnalysisService(db).analyze_finding(finding_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {exc}") from exc
