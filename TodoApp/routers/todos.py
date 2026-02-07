from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session
from .. import models

# from ..database import engine, Base
from ..database import SessionLocal
from typing import Annotated
from pydantic import BaseModel, Field
from ..routers import auth

router = APIRouter()


def get_db():
    db = None
    try:
        db = SessionLocal()
        yield db
    finally:
        if db is not None:
            db.close()


db_dependency = Annotated[Session, Depends(get_db)]


class TodoRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=250)
    priority: int = Field(..., ge=1, le=5)
    complete: bool = Field(default=False)


@router.get("/todo", status_code=status.HTTP_200_OK)
async def read_all_todo(db: db_dependency):
    todos = db.query(models.Todos).all()
    return todos


@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(db: db_dependency, todo_id: int = Path(gt=0)):
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo_model


@router.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(db: db_dependency, todo_request: TodoRequest):
    todo_model = models.Todos(**todo_request.model_dump())
    db.add(todo_model)
    db.commit()
    db.refresh(todo_model)
    return todo_model


@router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(
    db: db_dependency, todo_id: int = Path(gt=0), todo_request: TodoRequest = None
):
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    update_data = todo_request.model_dump()
    for key, value in update_data.items():
        setattr(todo_model, key, value)
    db.commit()
    db.refresh(todo_model)
    return todo_model


@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, todo_id: int = Path(gt=0)):
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(todo_model)
    db.commit()
    return
