from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date, time, datetime
import re


class TaskCreate(BaseModel):
    """Схема для создания задачи."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[date] = None  # YYYY-MM-DD (храним стандартно)
    due_time: Optional[str] = None  # HH:MM (валидируем 15-минутные слоты)
    priority: Optional[str] = "normal"  # low, normal, high, urgent
    color: Optional[str] = None  # Если не указан — авто по приоритету

    @validator('due_time')
    def validate_time_slot(cls, v):
        """Проверяем что время кратно 15 минутам."""
        if v is None:
            return v

        # Проверяем формат HH:MM
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
        """Проверяем допустимые значения приоритета."""
        allowed = ['low', 'normal', 'high', 'urgent']
        if v not in allowed:
            raise ValueError(f'Приоритет должен быть одним из: {", ".join(allowed)}')
        return v

    @validator('color', always=True)
    def set_default_color(cls, v, values):
        """Автоматически устанавливаем цвет по приоритету, если не указан."""
        if v is not None:
            return v

        priority_colors = {
            'low': '#FFF9C4',  # Светло-жёлтый
            'normal': '#BBDEFB',  # Голубой
            'high': '#E1BEE7',  # Сиреневый
            'urgent': '#FFCDD2',  # Красный (светло-красный)
        }

        priority = values.get('priority', 'normal')
        return priority_colors.get(priority, '#BBDEFB')


class TaskUpdate(BaseModel):
    """Схема для обновления задачи (все поля опциональны)."""
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    due_date: Optional[date] = None
    due_time: Optional[str] = None
    priority: Optional[str] = None
    color: Optional[str] = None

    @validator('due_time')
    def validate_time_slot(cls, v):
        """Проверяем что время кратно 15 минутам."""
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
        """Проверяем допустимые значения приоритета."""
        if v is None:
            return v
        allowed = ['low', 'normal', 'high', 'urgent']
        if v not in allowed:
            raise ValueError(f'Приоритет должен быть одним из: {", ".join(allowed)}')
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
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Pydantic v2