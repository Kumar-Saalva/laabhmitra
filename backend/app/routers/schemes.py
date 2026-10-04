from fastapi import APIRouter

from app import data, service
from app.engine.evaluate import is_stale

router = APIRouter(prefix="/api", tags=["schemes"])


@router.get("/schemes")
def list_schemes():
    """List schemes (id, name, status, last_verified)."""
    return [{"id": s["id"], "short_name": s["short_name"], "name": s["name"], "kind": s["kind"],
             "status": s["status"], "last_verified": s["last_verified"], "stale": is_stale(s["last_verified"])}
            for s in data.schemes().values()]


@router.get("/schemes/{scheme_id}")
def get_scheme(scheme_id: str):
    """The full scheme definition, exactly as stored in data/schemes.seed.json."""
    return service.get_scheme(scheme_id)


@router.get("/personas")
def list_personas():
    """Demo personas. Each one is also saved under its key (lakshmi, ravi, shabana) in demo mode."""
    return data.personas()
