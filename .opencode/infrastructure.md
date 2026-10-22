# Infrastructure

## Stack
- Backend: FastAPI + SQLAlchemy + JWT auth (backend/)
- Bot: python-telegram-bot (bot/, has own Dockerfile)
- Frontend: static site (frontend/site/) served by backend under /todo-api/

## Run (local)
- Backend: `uvicorn backend.app.main:app --reload --port 8000`
  (frontend hits http://127.0.0.1:8000/api locally)
- Bot: `python bot/main.py`
- No docker-compose observed in repo; bot has standalone Dockerfile.

## Config
- backend/app/config.py — DB, JWT, env
- bot/config.py — bot token, API base
- API_BASE/API_PATH in frontend/site/app.js:
  localhost → http://127.0.0.1:8000/api ; prod → origin + /todo-api/api