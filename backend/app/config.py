import os

# SQLite для разработки
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./todo.db"  # Файл базы данных будет создан рядом с приложением
)

DEFAULT_USER_ID = 1  # Временное решение для одного пользователя