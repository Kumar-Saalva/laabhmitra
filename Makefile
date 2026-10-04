PY ?= python3
VENV = backend/.venv/bin

.PHONY: setup api web dev test seed

setup:
	$(PY) -m venv backend/.venv
	$(VENV)/python -m pip install -r backend/requirements.txt
	npm --prefix frontend install

api:
	$(VENV)/python -m uvicorn app.main:app --app-dir backend --reload --port 8000

web:
	npm --prefix frontend run dev

# Runs the API and the web app together (Ctrl+C stops both).
dev:
	$(MAKE) -j2 api web

test:
	cd backend && .venv/bin/python -m pytest -q
	npm --prefix frontend run typecheck
	$(VENV)/python data/reference_engine.py

# Demo personas are saved automatically at API start when DEMO_MODE=true.
# This removes the local database so the next start is clean.
seed:
	rm -f backend/laabhmitra.db
