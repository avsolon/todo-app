from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date, time, datetime
import re
import html


class TaskCreate(BaseModel):
    """Схема для создания задачи."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    due_date: Optional[date] = None
    due_time: Optional[str] = None
    priority: Optional[str] = "normal"
    color: Optional[str] = None

    # === Поля повторения ===
    is_recurring: Optional[bool] = False
    recurrence_type: Optional[str] = None  # daily, weekly, monthly, yearly
    recurrence_interval: Optional[int] = 1  # Каждые N дней/недель/месяцев/лет
    recurrence_end_date: Optional[date] = None  # До какой даты повторять
    recurrence_count: Optional[int] = None  # Сколько раз повторить

    @validator('title')
    def sanitize_title(cls, v):
        v = re.sub(r'<[^>]*>', '', v)
        v = v.replace("'", "''")
        v = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', v)
        v = re.sub(r'\s+', ' ', v).strip()
        return v

    @validator('description')
    def sanitize_description(cls, v):
        if v is None:
            return v
        v = html.escape(v, quote=False)
        v = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', v)
        v = v.replace('\r\n', '\n').replace('\r', '\n')
        return v.strip()

    @validator('due_time')
    def validate_time_slot(cls, v):
        if v is None:
            return v
        if not re.match(r'^\d{2}:\d{2}$', v):
            raise ValueError('Время должно быть в формате HH:MM')
        hours, minutes = map(int, v.split(':'))
        if hours < 0 or hours > 23:
            raise ValueError('Часы должны быть от 00 до 23')
        if minutes not in [0, 15, 30, 45]:
            raise ValueError('Минуты должны быть 00, 15, 30 или 45')
        return v

    @validator('priority')
    def validate_priority(cls, v):
        allowed = ['low', 'normal', 'high', 'urgent']
        if v not in allowed:
            raise ValueError(f'Приоритет должен быть одним из: {", ".join(allowed)}')
        return v

    @validator('color')
    def validate_color(cls, v):
        if v is None:
            return v
        if not re.match(r'^#[0-9a-fA-F]{6}$', v):
            raise ValueError('Цвет должен быть в формате HEX (#RRGGBB)')
        return v

    @validator('recurrence_type')
    def validate_recurrence_type(cls, v):
        if v is None:
            return v
        allowed = ['daily', 'weekly', 'monthly', 'yearly']
        if v not in allowed:
            raise ValueError(f'Тип повторения должен быть одним из: {", ".join(allowed)}')
        return v


class TaskUpdate(BaseModel):
    """Схема для обновления задачи."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    completed: Optional[bool] = None
    due_date: Optional[date] = None
    due_time: Optional[str] = None
    priority: Optional[str] = None
    color: Optional[str] = None

    # Можно менять только дату/время (для drag & drop)
    # Повторение изменить нельзя (для простоты)

    @validator('title')
    def sanitize_title(cls, v):
        if v is None:
            return v
        v = re.sub(r'<[^>]*>', '', v)
        v = v.replace("'", "''")
        v = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', v)
        v = re.sub(r'\s+', ' ', v).strip()
        return v

    @validator('description')
    def sanitize_description(cls, v):
        if v is None:
            return v
        v = html.escape(v, quote=False)
        v = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', v)
        v = v.replace('\r\n', '\n').replace('\r', '\n')
        return v.strip()

    @validator('due_time')
    def validate_time_slot(cls, v):
        if v is None:
            return v
        if not re.match(r'^\d{2}:\d{2}$', v):
            raise ValueError('Время должно быть в формате HH:MM')
        hours, minutes = map(int, v.split(':'))
        if hours < 0 or hours > 23:
            raise ValueError('Часы должны быть от 00 до 23')
        if minutes not in [0, 15, 30, 45]:
            raise ValueError('Минуты должны быть 00, 15, 30 или 45')
        return v

    @validator('priority')
    def validate_priority(cls, v):
        if v is None:
            return v
        allowed = ['low', 'normal', 'high', 'urgent']
        if v not in allowed:
            raise ValueError(f'Приоритет должен быть одним из: {", ".join(allowed)}')
        return v

    @validator('color')
    def validate_color(cls, v):
        if v is None:
            return v
        if not re.match(r'^#[0-9a-fA-F]{6}$', v):
            raise ValueError('Цвет должен быть в формате HEX (#RRGGBB)')
        return v


class TaskResponse(BaseModel):
    """Схема ответа API."""
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    completed: bool
    due_date: Optional[date] = None
    due_time: Optional[str] = None
    priority: str
    color: str

    # Поля повторения
    is_recurring: bool = False
    recurrence_type: Optional[str] = None
    recurrence_interval: int = 1
    recurrence_end_date: Optional[date] = None
    recurrence_count: Optional[int] = None
    parent_task_id: Optional[int] = None

    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True