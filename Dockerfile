# One image that runs the whole app: build the web app, then serve it from the API.

FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/app backend/app
COPY data data
COPY --from=web /web/dist frontend/dist
ENV LLM_PROVIDER=mock DEMO_MODE=true LAABHMITRA_DB=/tmp/laabhmitra.db PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT}"]
