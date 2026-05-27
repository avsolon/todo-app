from sqlalchemy.orm import Session
from . import models, schemas

def get_tasks(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Task).filter(
        models.Task.user_id == user_id
    ).offset(skip).limit(limit).all()

def create_task(db: Session, task: schemas.TaskCreate, user_id: int):
    db_task = models.Task(**task.dict(), user_id=user_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task(db: Session, task_id: int, user_id: int, task_update: schemas.TaskUpdate):
    db_task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == user_id
    ).first()
    if not db_task:
        return None
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int, user_id: int):
    db_task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == user_id
    ).first()
    if db_task:
        db.delete(db_task)
        db.commit()
        return True
    return False