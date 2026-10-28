from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.finding import Finding
from app.services.ai.ai_security_service import AISecurityService
from app.services.ai.unified_analysis_service import UnifiedAnalysisService


router = APIRouter(prefix="/ai", tags=["AI Security Analyst"])


@router.get("/explain/{finding_id}")
def explain_finding(finding_id: int, db: Session = Depends(get_db)):
    finding = db.scalar(select(Finding).where(Finding.id == finding_id))
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found.")

    return {
        "finding_id": finding.id,
        "analysis": AISecurityService().explain_finding(
            {
                "id": finding.id,
                "asset_identifier": finding.asset_identifier,
                "finding_type": finding.finding_type,
                "severity": finding.severity,
                "title": finding.title,
                "description": finding.description,
            }
        ),
    }


@router.get("/summary")
def summarize_findings(db: Session = Depends(get_db)):
    findings = db.scalars(select(Finding).order_by(Finding.created_at.desc())).all()
    return AISecurityService().summarize_findings([
        {
            "id": finding.id,
            "severity": finding.severity,
            "title": finding.title,
            "asset_identifier": finding.asset_identifier,
        }
        for finding in findings
    ])


@router.get("/unified-analysis/{finding_id}")
def unified_analysis(finding_id: int, db: Session = Depends(get_db)):
    try:
        return UnifiedAnalysisService(db).analyze_finding(finding_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc
