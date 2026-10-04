import json

from fastapi import APIRouter
from pydantic import BaseModel, ValidationError

from app import data
from app.engine.derive import DERIVED_INPUTS
from app.engine.run import evaluate_all
from app.models import PROFILE_FIELDS, Profile, Scheme

router = APIRouter(prefix="/api/admin", tags=["admin"])

KNOWN_FIELDS = set(PROFILE_FIELDS) | set(DERIVED_INPUTS)


class TestScheme(BaseModel):
    scheme: dict


def validate(scheme: dict) -> tuple:
    """Return (errors, warnings). Errors stop the test run; warnings do not."""
    errors, warnings = [], []
    try:
        Scheme(**scheme)
    except ValidationError as e:
        errors = [f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in e.errors()]
        return errors, warnings
    source_ids = {s["id"] for s in scheme["sources"]}
    for c in scheme["criteria"]:
        conds = [c] + (c["when"].get("all", [c["when"]]) if c.get("when") else [])
        for cond in conds:
            if cond.get("field") not in KNOWN_FIELDS:
                warnings.append(f"criterion '{c['id']}': field '{cond.get('field')}' is not a profile field, so it will always be UNKNOWN")
        if c["source_ref"] not in source_ids:
            errors.append(f"criterion '{c['id']}': source_ref '{c['source_ref']}' is not in sources[]")
    if scheme["status"] == "verify" and not scheme.get("status_note"):
        warnings.append("status 'verify' should come with a status_note")
    return errors, warnings


@router.post("/test-scheme")
def test_scheme(body: TestScheme):
    """Rule tester: validate a pasted scheme JSON and run the three personas through it.

    Nothing is saved. To add the scheme for real, a human edits data/schemes.seed.json."""
    scheme = body.scheme
    errors, warnings = validate(scheme)
    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings, "results": []}
    schemes = {**data.schemes(), scheme["id"]: scheme}
    with open(data.DATA_DIR / "expected.json", encoding="utf-8") as f:
        expected = json.load(f)
    results = []
    for pid, persona in data.personas().items():
        try:
            e = evaluate_all(Profile(**persona).model_dump(exclude={"consent"}), schemes)[scheme["id"]]
        except Exception as error:      # e.g. comparing a number rule against a text value
            return {"valid": False, "errors": [f"rule failed for {pid}: {error}"], "warnings": warnings, "results": []}
        want = expected.get(pid, {}).get("schemes", {}).get(scheme["id"])
        results.append({
            "persona": pid, "display_name": persona["display_name"], "status": e["status"],
            "met": e["met"], "total": e["total"], "unknown": e["unknown"], "fails": e["fails"],
            "grant_min": e["estimate"]["grant_min"], "grant_max": e["estimate"]["grant_max"],
            "credit": e["estimate"]["credit"],
            "expected_status": want["status"] if want else None,
            "matches_expected": (want["status"] == e["status"] and want["fails"] == e["fails"]) if want else None,
        })
    return {"valid": True, "errors": [], "warnings": warnings, "results": results,
            "is_new": scheme["id"] not in data.schemes()}
