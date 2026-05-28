from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import DATABASE_URL


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Генератор сессий для FastAPI Depends."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Создаёт все таблицы и пользователя по умолчанию."""
    from .models import User

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == 1).first()
        if not user:
            db.add(User(id=1, username="default"))
            db.commit()
            print("✅ Создан пользователь по умолчанию (id=1)")
        print("✅ База данных инициализирована")
    finally:
        db.close()