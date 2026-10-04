from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import data, service, store
from app.engine import watch
from app.engine.run import evaluate_all
from app.llm import provider
from app.models import Profile

router = APIRouter(prefix="/api", tags=["profiles"])


class SaveProfile(BaseModel):
    profile: Profile
    profile_id: Optional[str] = None


class ExtractRequest(BaseModel):
    text: str
    lang: str = "en"


def save(profile: Profile, profile_id: Optional[str] = None) -> dict:
    """Save a profile, re-run the engine and record what changed since last time."""
    facts = service.profile_dict(profile)
    schemes = data.schemes()
    snapshot = watch.snapshot(evaluate_all(facts, schemes), schemes)
    previous = store.get_snapshot(profile_id) if profile_id else {}
    notes = watch.diff(previous, snapshot) if previous else []
    stored = {**facts, "consent": profile.consent.model_dump()}
    new_id = store.save_profile(stored, snapshot, notes, profile_id)
    return {"profile_id": new_id, "notifications": notes}


@router.post("/profiles")
def create_or_update_profile(body: SaveProfile):
    """Create/update a profile. Consent is required before anything is saved."""
    consent = body.profile.consent
    if consent is None or not consent.given:
        raise HTTPException(400, "Consent is required before a profile can be saved.")
    if not consent.timestamp:
        consent.timestamp = store.now()
    return save(body.profile, body.profile_id)


@router.get("/profiles/{profile_id}")
def get_profile(profile_id: str):
    saved = store.get_profile(profile_id)
    if saved is None:
        raise HTTPException(404, f"No saved profile with id '{profile_id}'.")
    return saved


@router.post("/extract")
def extract(body: ExtractRequest):
    """Free text or a voice transcript -> partial profile (LLM, or keyword mock offline)."""
    return provider.extract_profile(body.text)


@router.get("/watch/{profile_id}")
def watch_feed(profile_id: str):
    """Notifications feed: what improved after profile or scheme changes."""
    if store.get_profile(profile_id) is None:
        raise HTTPException(404, f"No saved profile with id '{profile_id}'.")
    schemes = data.schemes()
    notes = store.list_notifications(profile_id)
    for n in notes:
        n["short_name"] = schemes[n["scheme_id"]]["short_name"] if n["scheme_id"] in schemes else n["scheme_id"]
    return {"profile_id": profile_id, "notifications": notes}
