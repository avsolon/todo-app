# Todo Calendar — context

## Goal
Multi-platform todo calendar: FastAPI backend + Telegram bot + web frontend,
all sharing one task model.

## Architecture
- `backend/` — FastAPI, SQLAlchemy. API: `/api/tasks`, `/api/auth` (JWT).
  Models: Task (title, description, due_date, due_time, priority, color,
  completed bool, is_recurring + recurrence_*), User.
- `bot/` — python-telegram-bot. Flow states: CHOOSE_DATE, CHOOSE_TIME,
  ENTER_TITLE, ENTER_DESCRIPTION. Registers tasks for authed users.
- `frontend/site/` — static HTML/JS/CSS calendar (week view, mini-calendar,
  task cards, modal task editor). Served at `/todo-api/...` in prod,
  `http://127.0.0.1:8000` locally.

## Current task (completed)
Web: static task card + view/edit modal modes + «Выполнено» button +
green «Встреча/Конференция» priority in legend; bot time buttons fixed.

## Key files
- `bot/main.py` — time-selection regex + flow handlers
- `frontend/site/app.js` — state, PRIORITY_*, createTaskCard, openTaskModal,
  setModalMode, handleFormSubmit
- `frontend/site/index.html` — modal form, sidebar legend
- `frontend/site/style.css` — task-card + modal styles
- `backend/app/{models,schemas,crud}.py`, `backend/app/routers/tasks.py`