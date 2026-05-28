from .database import SessionLocal
from .config import DEFAULT_USER_ID


async def get_db():
    """Зависимость: сессия БД."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user():
    """
    Получить текущего пользователя.
    Пока заглушка — всегда возвращает пользователя с ID=1.
    В будущем: проверка JWT-токена.
    """
    return {"user_id": DEFAULT_USER_ID}