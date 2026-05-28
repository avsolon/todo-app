from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, time, datetime


class TaskCreate(BaseModel):
    """Схема для создания задачи."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[date] = None      # YYYY-MM-DD
    due_time: Optional[time] = None      # HH:MM
    priority: Optional[str] = "normal"   # low, normal, high
    color: Optional[str] = "#4285f4"     # HEX цвет


class TaskUpdate(BaseModel):
    """Схема для обновления задачи (все поля опциональны)."""
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    priority: Optional[str] = None
    color: Optional[str] = None


class TaskResponse(BaseModel):
    """Схема ответа API."""
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    completed: bool
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    priority: str
    color: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Pydantic v2


class TasksByDate(BaseModel):
    """Группировка задач по датам."""
    date: date
    tasks: list[TaskResponse]