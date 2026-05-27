from fastapi import Depends
from .database import SessionLocal
from .config import DEFAULT_USER_ID

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user():
    # В будущем здесь будет проверка токена/сессии
    # Сейчас всегда возвращаем дефолтного пользователя
    return {"user_id": DEFAULT_USER_ID}