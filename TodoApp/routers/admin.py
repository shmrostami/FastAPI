from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session
from .. import models
from ..database import SessionLocal
from typing import Annotated
from pydantic import BaseModel, Field
from ..routers import auth
from .auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


def get_db():
    db = None
    try:
        db = SessionLocal()
        yield db
    finally:
        if db is not None:
            db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("/todo", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):
    """
    Admin endpoint to return all todos by all users.
    Only users with role 'admin' can access.
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    if user.get("user_role") != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized: Admins only")

    todos = db.query(models.Todos).all()
    return todos


@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)
):
    """
    Admin endpoint to delete any todo by its ID.
    Only users with role 'admin' can access.
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    if user.get("user_role") != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized: Admins only")

    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    db.delete(todo_model)
    db.commit()
    return
