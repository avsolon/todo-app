from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date, time, datetime
import re
import html


class TaskCreate(BaseModel):
    """Схема для создания задачи с защитой от инъекций."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    due_date: Optional[date] = None
    due_time: Optional[str] = None
    priority: Optional[str] = "normal"
    color: Optional[str] = None

    @validator('title')
    def sanitize_title(cls, v):
        """Очистка заголовка от опасных символов."""
        # Удаляем HTML-теги
        v = re.sub(r'<[^>]*>', '', v)
        # Удаляем потенциально опасные SQL-символы (доп. защита)
        v = v.replace("'", "''")
        # Удаляем управляющие символы
        v = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', v)
        # Обрезаем множественные пробелы
        v = re.sub(r'\s+', ' ', v).strip()
        return v

    @validator('description')
    def sanitize_description(cls, v):
        """Очистка описания от опасных символов."""
        if v is None:
            return v
        # Экранируем HTML
        v = html.escape(v, quote=False)
        # Удаляем управляющие символы (кроме переноса строки)
        v = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', v)
        # Оставляем только безопасные переносы строк
        v = v.replace('\r\n', '\n').replace('\r', '\n')
        return v.strip()

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
        allowed = ['low', 'normal', 'high', 'urgent']
        if v not in allowed:
            raise ValueError(f'Приоритет должен быть одним из: {", ".join(allowed)}')
        return v

    @validator('color')
    def validate_color(cls, v):
        """Проверяем формат цвета."""
        if v is None:
            return v
        if not re.match(r'^#[0-9a-fA-F]{6}$', v):
            raise ValueError('Цвет должен быть в формате HEX (#RRGGBB)')
        return v


class TaskUpdate(BaseModel):
    """Схема для обновления задачи с защитой."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    completed: Optional[bool] = None
    due_date: Optional[date] = None
    due_time: Optional[str] = None
    priority: Optional[str] = None
    color: Optional[str] = None

    @validator('title')
    def sanitize_title(cls, v):
        """Очистка заголовка."""
        if v is None:
            return v
        v = re.sub(r'<[^>]*>', '', v)
        v = v.replace("'", "''")
        v = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', v)
        v = re.sub(r'\s+', ' ', v).strip()
        return v

    @validator('description')
    def sanitize_description(cls, v):
        """Очистка описания."""
        if v is None:
            return v
        v = html.escape(v, quote=False)
        v = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', v)
        v = v.replace('\r\n', '\n').replace('\r', '\n')
        return v.strip()

    @validator('due_time')
    def validate_time_slot(cls, v):
        """Проверяем время."""
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
        """Проверяем приоритет."""
        if v is None:
            return v
        allowed = ['low', 'normal', 'high', 'urgent']
        if v not in allowed:
            raise ValueError(f'Приоритет должен быть одним из: {", ".join(allowed)}')
        return v

    @validator('color')
    def validate_color(cls, v):
        """Проверяем цвет."""
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
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True