from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app import service
from app.engine import affordability
from app.models import Profile

router = APIRouter(prefix="/api", tags=["evaluate"])


@router.post("/evaluate")
def evaluate(body: service.ProfileRef):
    """{profile or profile_id} -> per-scheme results + estimates + tiers + opportunity map."""
    profile = service.load_profile(body.profile, body.profile_id)
    return service.evaluate(profile, body.lang)


@router.get("/opportunity-map/{profile_id}")
def opportunity_map(profile_id: str, lang: str = "en"):
    """Buckets (grants, credit, fee savings, non-monetary) + best paths + fix plan."""
    profile = service.load_profile(None, profile_id)
    return service.evaluate(profile, lang)["opportunity_map"]


class AffordabilityRequest(BaseModel):
    profile: Optional[Profile] = None
    profile_id: Optional[str] = None
    scheme_id: str
    annual_rate: Optional[float] = Field(None, ge=0, le=0.6)       # fraction: 0.12 = 12%
    tenure_months: Optional[int] = Field(None, ge=1, le=360)


@router.post("/affordability")
def check_affordability(body: AffordabilityRequest):
    """Re-run the affordability check for one scheme with the merchant's own rate and tenure.

    The principal always comes from the engine's estimate; this never changes eligibility."""
    profile = service.load_profile(body.profile, body.profile_id)
    service.get_scheme(body.scheme_id)
    result = service.result_for(profile, body.scheme_id)
    out = affordability.check(profile, body.scheme_id, result["estimate"]["credit"],
                              body.annual_rate, body.tenure_months)
    if out is None:
        raise HTTPException(404, "This scheme has no loan to check.")
    return out
