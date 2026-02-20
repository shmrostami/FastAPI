from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session
from .. import models
from ..database import SessionLocal
from typing import Annotated
from pydantic import BaseModel, Field
from ..routers import auth
from .auth import get_current_user
import bcrypt

router = APIRouter(prefix="/user", tags=["user"])


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

# bcrypt has a 72-byte limit; truncate to avoid ValueError
BCRYPT_MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:BCRYPT_MAX_PASSWORD_BYTES]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")


class UserVerificatoin(BaseModel):
    password: str
    new_password: str = Field(min_length=6)


@router.get("/", status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency, db: db_dependency):
    """
    Returns the current logged-in user's information.
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    user_model = (
        db.query(models.Users).filter(models.Users.id == user.get("id")).first()
    )
    if user_model is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user_model
    # return {
    #     "id": user_model.id,
    #     "username": user_model.username,
    #     "email": user_model.email,
    #     "first_name": user_model.first_name,
    #     "last_name": user_model.last_name,
    #     "role": user_model.role,
    #     "is_active": user_model.is_active
    # }


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    user: user_dependency, db: db_dependency, user_verification: UserVerificatoin
):
    """
    Allows the logged-in user to change their password.
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    user_model = (
        db.query(models.Users).filter(models.Users.id == user.get("id")).first()
    )
    if user_model is None:
        raise HTTPException(status_code=404, detail="User not found")

    pwd_bytes = user_verification.password.encode("utf-8")[:BCRYPT_MAX_PASSWORD_BYTES]
    if not bcrypt.checkpw(pwd_bytes, user_model.hashed_password.encode("utf-8")):
        raise HTTPException(status_code=403, detail="Incorrect current password")

    # hash the new password
    new_pwd_bytes = user_verification.new_password.encode("utf-8")[
        :BCRYPT_MAX_PASSWORD_BYTES
    ]
    new_hashed_pw = bcrypt.hashpw(new_pwd_bytes, bcrypt.gensalt()).decode("utf-8")

    user_model.hashed_password = new_hashed_pw
    db.commit()
    return
