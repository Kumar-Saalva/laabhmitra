from typing import Optional

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from app import service
from app.engine import project_report
from app.llm import provider
from app.models import Profile
from app.pdf import project_report as report_pdf

router = APIRouter(prefix="/api", tags=["project report"])


class ReportRequest(BaseModel):
    profile_id: Optional[str] = None
    profile: Optional[Profile] = None
    annual_rate: Optional[float] = Field(None, ge=0, le=0.6)
    tenure_months: Optional[int] = Field(None, ge=1, le=360)


def build(profile: dict, annual_rate=None, tenure_months=None) -> dict:
    report = project_report.build(profile, service.get_scheme("pmegp"), annual_rate, tenure_months)
    if report["complete"]:
        report["narrative"] = provider.draft_project_narrative(profile, report)
    return report


@router.post("/project-report")
def project_report_json(body: ReportRequest):
    """Bank-style project report draft as JSON. All numbers are computed in code;
    the narrative sections are checked by the guard. If inputs are missing, says which."""
    profile = service.load_profile(body.profile, body.profile_id)
    return build(profile, body.annual_rate, body.tenure_months)


@router.get("/project-report/{profile_id}/pdf")
def project_report_pdf(profile_id: str):
    """The same report as a PDF, watermarked DRAFT on every page."""
    profile = service.load_profile(None, profile_id)
    report = build(profile)
    if not report["complete"]:
        raise HTTPException(400, "Project details are incomplete: " + ", ".join(report["missing"]))
    pdf = report_pdf.build_pdf(profile, report, report["narrative"])
    return Response(pdf, media_type="application/pdf", headers={
        "Content-Disposition": 'attachment; filename="laabhmitra-project-report-draft.pdf"'})
