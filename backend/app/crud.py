from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date, datetime, timedelta
from . import models, schemas


def get_tasks(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        due_date: date = None,
        start_date: date = None,
        end_date: date = None
):
    """
    Получить список задач с возможностью фильтрации по датам.

    - due_date: задачи на конкретную дату
    - start_date, end_date: задачи в диапазоне дат
    """
    query = db.query(models.Task).filter(models.Task.user_id == user_id)

    if due_date:
        query = query.filter(models.Task.due_date == due_date)
    elif start_date and end_date:
        query = query.filter(
            and_(
                models.Task.due_date >= start_date,
                models.Task.due_date <= end_date
            )
        )

    return query.order_by(
        models.Task.due_time.asc().nullsfirst(),  # Сначала без времени
        models.Task.priority.desc(),  # Высокий приоритет выше
        models.Task.created_at.desc()
    ).offset(skip).limit(limit).all()


def get_tasks_grouped_by_date(
        db: Session,
        user_id: int,
        start_date: date,
        end_date: date
):
    """
    Получить задачи, сгруппированные по датам.
    Возвращает словарь: {дата: [задачи]}
    """
    tasks = db.query(models.Task).filter(
        and_(
            models.Task.user_id == user_id,
            models.Task.due_date >= start_date,
            models.Task.due_date <= end_date
        )
    ).order_by(
        models.Task.due_time.asc().nullsfirst(),
        models.Task.priority.desc()
    ).all()

    # Группируем по датам
    grouped = {}
    for task in tasks:
        if task.due_date:
            key = task.due_date.isoformat()
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(task)

    return grouped


def create_task(db: Session, task: schemas.TaskCreate, user_id: int):
    """Создать новую задачу."""
    db_task = models.Task(**task.model_dump(), user_id=user_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task(db: Session, task_id: int, user_id: int, task_update: schemas.TaskUpdate):
    """Обновить задачу."""
    db_task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == user_id
    ).first()

    if not db_task:
        return None

    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)

    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int, user_id: int):
    """Удалить задачу."""
    db_task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == user_id
    ).first()
    if db_task:
        db.delete(db_task)
        db.commit()
        return True
    return False


def get_task(db: Session, task_id: int, user_id: int):
    """Получить одну задачу по ID."""
    return db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == user_id
    ).first()