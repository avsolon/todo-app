from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date, Time
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False)

    # Новые поля для календаря
    due_date = Column(Date, nullable=True, index=True)  # Дата выполнения (ДД.ММ.ГГГГ)
    due_time = Column(Time, nullable=True)  # Время выполнения (ЧЧ:ММ)

    priority = Column(String, default="normal")  # Приоритет: low, normal, high
    color = Column(String, default="#4285f4")  # Цвет для отображения в календаре

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())