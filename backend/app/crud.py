from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from . import models, schemas

PRIORITY_COLORS = {
    'low': '#FFF9C4',
    'normal': '#BBDEFB',
    'high': '#E1BEE7',
    'urgent': '#FFCDD2',
}


def generate_recurring_dates(start_date, rec_type, interval, end_date=None, count=None):
    """
    Генерирует даты повторяющихся задач.
    Возвращает список дат.
    """
    dates = []
    current = start_date
    occurrences = 0

    while True:
        if end_date and current > end_date:
            break
        if count and occurrences >= count:
            break

        dates.append(current)
        occurrences += 1

        if rec_type == 'daily':
            current = current + timedelta(days=interval)
        elif rec_type == 'weekly':
            current = current + timedelta(weeks=interval)
        elif rec_type == 'monthly':
            current = current + relativedelta(months=interval)
        elif rec_type == 'yearly':
            current = current + relativedelta(years=interval)
        else:
            break

        # Защита от бесконечного цикла
        if occurrences > 365:
            break

    return dates


def get_tasks(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        due_date: date = None,
        start_date: date = None,
        end_date: date = None
):
    """Получить список задач с фильтрацией."""
    query = db.query(models.Task).filter(models.Task.user_id == user_id)

    # Исключаем дочерние задачи (они создаются автоматически)
    query = query.filter(models.Task.parent_task_id == None)

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
        models.Task.due_time.asc().nullsfirst(),
        models.Task.priority.desc(),
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
    Для повторяющихся задач создаются виртуальные экземпляры.
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

    grouped = {}

    for task in tasks:
        if task.parent_task_id:
            continue  # Пропускаем дочерние

        if task.is_recurring and task.due_date and task.recurrence_type:
            # Генерируем все даты повторения в диапазоне
            recurring_dates = generate_recurring_dates(
                task.due_date,
                task.recurrence_type,
                task.recurrence_interval,
                task.recurrence_end_date,
                task.recurrence_count
            )

            for rec_date in recurring_dates:
                if start_date <= rec_date <= end_date:
                    key = rec_date.isoformat()
                    if key not in grouped:
                        grouped[key] = []

                    # Создаём виртуальную копию задачи для этой даты
                    virtual_task = models.Task(
                        id=task.id,
                        user_id=task.user_id,
                        title=task.title,
                        description=task.description,
                        completed=task.completed,
                        due_date=rec_date,
                        due_time=task.due_time,
                        priority=task.priority,
                        color=task.color,
                        is_recurring=True,
                        recurrence_type=task.recurrence_type,
                        recurrence_interval=task.recurrence_interval,
                        parent_task_id=None,
                        created_at=task.created_at,
                    )
                    grouped[key].append(virtual_task)
        else:
            # Обычная задача
            if task.due_date:
                key = task.due_date.isoformat()
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(task)

    return grouped


def create_task(db: Session, task: schemas.TaskCreate, user_id: int):
    """Создать новую задачу."""
    task_data = task.model_dump()

    if not task_data.get('color'):
        task_data['color'] = PRIORITY_COLORS.get(
            task_data.get('priority', 'normal'), '#BBDEFB'
        )

    db_task = models.Task(**task_data, user_id=user_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task(db: Session, task_id: int, user_id: int, task_update: schemas.TaskUpdate):
    """Обновить задачу (для Drag & Drop меняем дату/время)."""
    db_task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == user_id
    ).first()

    if not db_task:
        return None

    update_data = task_update.model_dump(exclude_unset=True)

    if 'priority' in update_data and 'color' not in update_data:
        update_data['color'] = PRIORITY_COLORS.get(
            update_data['priority'], '#BBDEFB'
        )

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