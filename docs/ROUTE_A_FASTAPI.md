# Route A: Dual-Loop FastAPI (Single Supported Entrypoint)

## What runs in Route A

- Backend: FastAPI + LangGraph (library usage) dual-loop supervisor
- Frontend (dev): Vite on `http://localhost:5173/app/`
- Frontend (prod/Docker): served by FastAPI under `/app` when `frontend/dist` exists

## Start (local dev)

Backend:

```bash
cd backend
uv sync
uv run uvicorn src.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open:

```
http://localhost:5173/app/
```

## Docker

```bash
docker compose up --build
```

Backend (and built frontend) will be available at:

```
http://localhost:8000/app/
```

## Notes

- Legacy `backend/src/agent/*` demo code has been removed to keep Route A as the only supported path.
