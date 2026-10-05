"""LaabhMitra API. AI explains. Rules decide. Government sources confirm."""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

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


# Hosted mode: when the frontend has been built (frontend/dist), this one service also
# serves the web app, so a single web address runs everything. In development the Vite
# dev server serves the frontend instead and this block does nothing.
DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

if DIST.is_dir():
    @app.get("/{path:path}", include_in_schema=False)
    def web_app(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "Not Found")
        file = (DIST / path).resolve()
        if path and file.is_file() and DIST in file.parents:
            return FileResponse(file)
        return FileResponse(DIST / "index.html")      # the React router handles the page
