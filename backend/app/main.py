"""LaabhMitra API. AI explains. Rules decide. Government sources confirm."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import data, store
from app.llm.provider import get_provider
from app.models import Consent, Profile
from app.routers import admin, evaluate, explain, pack, profiles, project, schemes

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"


def preload_personas():
    """Demo mode: save Lakshmi, Ravi and Shabana under their own ids so every page works at once."""
    for pid, persona in data.personas().items():
        if store.get_profile(pid) is None:
            consent = Consent(given=True, timestamp=store.now(), purposes=["demo"])
            profiles.save(Profile(**persona, consent=consent), pid)


@asynccontextmanager
async def lifespan(app: FastAPI):
    store.init_db()
    if DEMO_MODE:
        preload_personas()
    yield


app = FastAPI(title="LaabhMitra", version="0.1.0", lifespan=lifespan,
              description="Government benefits copilot for small businesses. Information only; "
                          "not affiliated with the Government of India.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])

for module in (schemes, profiles, evaluate, explain, pack, project, admin):
    app.include_router(module.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "schemes": len(data.schemes()), "llm_provider": get_provider().name,
            "demo_mode": DEMO_MODE}
