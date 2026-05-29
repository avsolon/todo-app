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

    due_date = Column(Date, nullable=True, index=True)
    due_time = Column(String, nullable=True)

    priority = Column(String, default="normal")
    color = Column(String, default="#BBDEFB")

    # === Поля повторения ===
    is_recurring = Column(Boolean, default=False)  # Повторяющаяся
    recurrence_type = Column(String, nullable=True)  # daily, weekly, monthly, yearly
    recurrence_interval = Column(Integer, default=1)  # Каждые N дней/недель/месяцев/лет
    recurrence_end_date = Column(Date, nullable=True)  # Дата окончания повторений
    recurrence_count = Column(Integer, nullable=True)  # Количество повторений
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)  # Ссылка на родительскую задачу

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())