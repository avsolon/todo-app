from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import tasks

# Создаём приложение с отключенным редиректом слешей
app = FastAPI(
    title="Todo Calendar API",
    description="Планировщик дел с календарём",
    version="1.0.0",
    redirect_slashes=False,
)

# Разрешаем запросы с фронтенда (для разработки)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(tasks.router)


@app.get("/")
@app.get("/health")
def health():
    """Проверка работоспособности и корневой эндпоинт."""
    return {
        "status": "ok",
        "database": "sqlite",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "api": "/api/tasks",
            "calendar": "/api/tasks/calendar"
        }
    }


# Инициализируем БД при старте
@app.on_event("startup")
async def startup_event():
    init_db()
    print("✅ Приложение готово к работе!")