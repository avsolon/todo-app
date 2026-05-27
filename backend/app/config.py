import os

DATABASE_URL = os.getenv("DATABASE_URL", "postrgesql://todo-user:todo_pass@db:5432/todo_db")
DEFAULT_USER_ID = 1  # Временно для одного пользователя