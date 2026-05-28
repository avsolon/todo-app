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

    # Дата и время выполнения
    due_date = Column(Date, nullable=True, index=True)  # Храним как Date (YYYY-MM-DD)
    due_time = Column(String, nullable=True)  # Храним как String "HH:MM" для простоты

    priority = Column(String, default="normal")  # low, normal, high, urgent
    color = Column(String, default="#BBDEFB")  # Цвет в HEX

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())