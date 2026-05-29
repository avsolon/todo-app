from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from .. import crud, schemas
from ..dependencies import get_db, get_current_user


router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.get("", response_model=List[schemas.TaskResponse])
@router.get("/", response_model=List[schemas.TaskResponse])
def list_tasks(
        due_date: Optional[date] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    return crud.get_tasks(
        db, user_id=user_id,
        skip=skip, limit=limit,
        due_date=due_date,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/calendar", response_model=dict)
@router.get("/calendar/", response_model=dict)
def get_calendar_tasks(
        start_date: date = Query(..., description="Начало диапазона"),
        end_date: date = Query(..., description="Конец диапазона"),
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    grouped = crud.get_tasks_grouped_by_date(db, user_id, start_date, end_date)

    result = {}
    for date_str, tasks in grouped.items():
        result[date_str] = [
            schemas.TaskResponse.model_validate(task) for task in tasks
        ]
    return result


@router.get("/{task_id}", response_model=schemas.TaskResponse)
def get_task(
        task_id: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    task = crud.get_task(db, task_id, user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
        task: schemas.TaskCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    return crud.create_task(db, task, user_id)


@router.put("/{task_id}", response_model=schemas.TaskResponse)
def update_task(
        task_id: int,
        task_update: schemas.TaskUpdate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    updated = crud.update_task(db, task_id, user_id, task_update)
    if updated is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
        task_id: int,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    success = crud.delete_task(db, task_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")