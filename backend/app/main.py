from fastapi import FastAPI
from .database import engine, Base
from .routers import tasks
from .models import User
from sqlalchemy.orm import Session
from .database import SessionLocal
from .config import DEFAULT_USER_ID

app = FastAPI(title="Todo App API")

# Создаём таблицы при старте (для простоты; в production использовать Alembic)
Base.metadata.create_all(bind=engine)

# Создаём дефолтного пользователя, если его ещё нет
def init_default_user():
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == DEFAULT_USER_ID).first()
        if not user:
            db.add(User(id=DEFAULT_USER_ID, username="default"))
            db.commit()
    finally:
        db.close()

init_default_user()

app.include_router(tasks.router)

@app.get("/health")
def health():
    return {"status": "ok"}