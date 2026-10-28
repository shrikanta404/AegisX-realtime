from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.evidence import Evidence
from app.models.finding import Finding
from app.services.evidence_service import EvidenceService
from app.services.finding_review_service import FindingReviewService


router = APIRouter(prefix="/findings", tags=["Findings"])


class FalsePositiveRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)


class EvidenceRequest(BaseModel):
    evidence_type: str = Field(min_length=1, max_length=100)
    evidence_data: object


@router.get("")
def list_findings(
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    finding_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = select(Finding).order_by(Finding.created_at.desc()).limit(limit)
    if status:
        query = query.where(Finding.status == status)
    if severity:
        query = query.where(Finding.severity == severity)
    if finding_type:
        query = query.where(Finding.finding_type == finding_type)

    rows = db.scalars(query).all()
    return [serialize_finding(item) for item in rows]


@router.get("/{finding_id}")
def get_finding(finding_id: int, db: Session = Depends(get_db)):
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found.")
    return serialize_finding(finding, include_evidence=True, db=db)


@router.post("/{finding_id}/evidence")
def add_evidence(
    finding_id: int,
    request: EvidenceRequest,
    db: Session = Depends(get_db),
):
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found.")
    evidence = EvidenceService(db).create_evidence(
        finding=finding,
        evidence_type=request.evidence_type,
        evidence_data=request.evidence_data,
        commit=True,
    )
    return {
        "status": "created",
        "evidence_id": evidence.id,
        "finding_id": finding.id,
    }


@router.patch("/{finding_id}/false-positive")
def mark_false_positive(
    finding_id: int,
    request: FalsePositiveRequest,
    x_actor: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    try:
        finding = FindingReviewService(db).mark_false_positive(
            finding_id=finding_id,
            reason=request.reason,
            actor=x_actor,
        )
        return {
            "status": "updated",
            "finding_id": finding.id,
            "false_positive": finding.false_positive,
            "status_value": finding.status,
            "reason": finding.false_positive_reason,
        }
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


def serialize_finding(finding: Finding, include_evidence: bool = False, db: Session | None = None):
    result = {
        "id": finding.id,
        "change_id": finding.change_id,
        "asset_identifier": finding.asset_identifier,
        "finding_type": finding.finding_type,
        "severity": finding.severity,
        "title": finding.title,
        "description": finding.description,
        "status": finding.status,
        "false_positive": finding.false_positive,
        "false_positive_reason": finding.false_positive_reason,
        "created_at": finding.created_at,
        "updated_at": finding.updated_at,
    }
    if include_evidence and db is not None:
        evidence = db.scalars(
            select(Evidence)
            .where(Evidence.finding_id == finding.id)
            .order_by(Evidence.collected_at.desc())
        ).all()
        result["evidence"] = [
            {
                "id": item.id,
                "evidence_type": item.evidence_type,
                "evidence_data": item.evidence_data,
                "collected_at": item.collected_at,
            }
            for item in evidence
        ]
    return result
