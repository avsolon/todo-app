#!/usr/bin/env python3
"""
Скрипт для запуска сервера в PyCharm.
Просто нажмите Run на этом файле.
"""
import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Запуск Todo Calendar API")
    print("=" * 60)
    print(f"📖 Swagger документация: http://127.0.0.1:8000/docs")
    print(f"💚 Health check: http://127.0.0.1:8000/health")
    print(f"📋 API: http://127.0.0.1:8000/api/tasks")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )