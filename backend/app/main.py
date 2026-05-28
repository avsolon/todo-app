from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from collections import defaultdict
import time

from .database import init_db
from .routers import tasks

# Создаём приложение
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

# ===== Rate Limiting (защита от DDoS/перебора) =====
# Простое ограничение: не более 60 запросов в минуту с одного IP
rate_limit_store = defaultdict(list)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Ограничение частоты запросов."""
    # Пропускаем статические файлы и документацию
    if request.url.path in ["/docs", "/openapi.json", "/health"]:
        return await call_next(request)

    client_ip = request.client.host
    current_time = time.time()

    # Очищаем старые записи
    rate_limit_store[client_ip] = [
        t for t in rate_limit_store[client_ip]
        if current_time - t < 60
    ]

    # Проверяем лимит
    if len(rate_limit_store[client_ip]) >= 60:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Слишком много запросов. Попробуйте позже."}
        )

    rate_limit_store[client_ip].append(current_time)

    return await call_next(request)


# Подключаем роутеры
app.include_router(tasks.router)


@app.get("/")
@app.get("/health")
def health():
    """Проверка работоспособности."""
    return {
        "status": "ok",
        "database": "sqlite",
        "version": "1.0.0",
    }


@app.on_event("startup")
async def startup_event():
    init_db()
    print("✅ Приложение готово к работе!")