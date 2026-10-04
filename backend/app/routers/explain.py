from typing import Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app import service
from app.llm import provider
from app.models import Profile

router = APIRouter(prefix="/api", tags=["explain"])


class ExplainRequest(BaseModel):
    profile_id: Optional[str] = None
    profile: Optional[Profile] = None
    scheme_id: str
    lang: str = "en"
    kind: Literal["why", "why_not"] = "why"


@router.post("/explain")
def explain(body: ExplainRequest):
    """Plain-language 'why' or 'why not'. The engine result is computed first; the text only rewords it."""
    profile = service.load_profile(body.profile, body.profile_id)
    scheme = service.get_scheme(body.scheme_id)
    result = service.result_for(profile, body.scheme_id)
    out = provider.explain(body.kind, profile, scheme, result, body.lang)
    return {**out, "status": result["status"], "scheme_id": body.scheme_id, "kind": body.kind}
