"""Shared helpers for the routers: load a profile, run the engine, attach scheme card info."""
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel

from app import data, i18n, store
from app.engine.run import full_result
from app.models import Profile


class ProfileRef(BaseModel):
    """Either a full profile or the id of a saved one."""
    profile: Optional[Profile] = None
    profile_id: Optional[str] = None
    lang: str = "en"


def profile_dict(profile: Profile) -> dict:
    """The dict the engine works on. Consent is kept apart from the business facts."""
    return profile.model_dump(exclude={"consent"})


def load_profile(ref_profile: Optional[Profile], profile_id: Optional[str]) -> dict:
    if ref_profile is not None:
        return profile_dict(ref_profile)
    if profile_id:
        saved = store.get_profile(profile_id)
        if saved is None:
            raise HTTPException(404, f"No saved profile with id '{profile_id}'.")
        return profile_dict(Profile(**saved))
    raise HTTPException(422, "Send either 'profile' or 'profile_id'.")


def get_scheme(scheme_id: str) -> dict:
    scheme = data.schemes().get(scheme_id)
    if scheme is None:
        raise HTTPException(404, f"No scheme with id '{scheme_id}'.")
    return scheme


def scheme_card(scheme: dict, lang: str = "en") -> dict:
    """What a scheme card needs: name, status badge, source, link, benefit buckets."""
    return {
        "id": scheme["id"], "short_name": scheme["short_name"], "name": scheme["name"],
        "level": scheme["level"], "ministry": scheme.get("ministry"), "kind": scheme["kind"],
        "status": scheme["status"], "status_note": scheme.get("status_note"),
        "summary_plain": i18n.summary(lang, scheme), "benefits": scheme.get("benefits", []),
        "documents": scheme.get("documents", []), "application": scheme["application"],
        "sources": scheme["sources"], "last_verified": scheme["last_verified"],
        "warning": scheme.get("warning"), "conflict_note": scheme.get("conflict_note"),
    }


def evaluate(profile: dict, lang: str = "en", schemes: Optional[dict] = None) -> dict:
    """Run the engine, then translate labels. Translation never touches a status or an amount."""
    schemes = schemes or data.schemes()
    conflicts = [{**c, "message": i18n.conflict_message(lang, c)} for c in data.conflicts()]
    out = full_result(profile, schemes, conflicts)
    for result in out["results"]:
        scheme = schemes[result["scheme_id"]]
        result["scheme"] = scheme_card(scheme, lang)
        for c in result["criteria"]:
            c["label"] = i18n.criterion_label(lang, scheme["id"], c)
            if c.get("fix"):
                c["fix"] = {**c["fix"], "label": i18n.fix_label(lang, c["fix"])}
    for step in out["opportunity_map"]["fix_plan"]:
        step["label"] = i18n.fix_label(lang, step)
        step["unlock_names"] = [schemes[s]["short_name"] for s in step["unlocks"]]
    for path in out["opportunity_map"]["best_paths"]:
        path["names"] = [schemes[s]["short_name"] for s in path["schemes"]]
    return out


def result_for(profile: dict, scheme_id: str) -> dict:
    """The (English, untranslated) engine result for one scheme."""
    from app.engine.run import evaluate_all
    return evaluate_all(profile, data.schemes())[scheme_id]
