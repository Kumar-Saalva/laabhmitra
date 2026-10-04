from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from app import service, store
from app.llm import provider
from app.models import Profile
from app.pdf import pack as pdf_pack

router = APIRouter(prefix="/api", tags=["pack"])


class PackRequest(BaseModel):
    profile_id: Optional[str] = None
    profile: Optional[Profile] = None
    scheme_id: str
    lang: str = "en"


class StatusUpdate(BaseModel):
    profile_id: str
    scheme_id: str
    status: Literal["not_started", "docs_ready", "applied", "sanctioned", "received"]
    amount_received_inr: Optional[int] = Field(None, ge=0)


def build(body: PackRequest) -> dict:
    profile = service.load_profile(body.profile, body.profile_id)
    scheme = service.get_scheme(body.scheme_id)
    result = service.result_for(profile, body.scheme_id)
    draft = provider.draft_pack(profile, scheme, result)
    return {"profile": profile, "scheme": scheme, "result": result, "draft": draft,
            "checklist": pdf_pack.checklist(profile, scheme)}


@router.post("/pack")
def pack_pdf(body: PackRequest):
    """Application pack as a PDF: checklist, how to apply, draft cover note (watermarked DRAFT)."""
    p = build(body)
    pdf = pdf_pack.build_pdf(p["profile"], p["scheme"], p["result"], p["draft"]["text"], p["checklist"])
    return Response(pdf, media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="laabhmitra-{body.scheme_id}-draft.pdf"'})


@router.post("/pack/preview")
def pack_preview(body: PackRequest):
    """The same pack as JSON, for the on-screen preview."""
    p = build(body)
    tracker = store.get_pack_status(body.profile_id, body.scheme_id) if body.profile_id else None
    return {"scheme": service.scheme_card(p["scheme"], body.lang), "status": p["result"]["status"],
            "checklist": p["checklist"], "draft": p["draft"], "tracker": tracker}


@router.get("/pack/status/{profile_id}")
def pack_statuses(profile_id: str):
    """Outcome tracker for every scheme this merchant has touched."""
    return store.list_pack_statuses(profile_id)


@router.post("/pack/status")
def set_pack_status(body: StatusUpdate):
    """Status tracker: Not started / Docs ready / Applied / Sanctioned / Received (with rupees received)."""
    if store.get_profile(body.profile_id) is None:
        raise HTTPException(404, f"No saved profile with id '{body.profile_id}'.")
    service.get_scheme(body.scheme_id)
    return store.set_pack_status(body.profile_id, body.scheme_id, body.status, body.amount_received_inr)
