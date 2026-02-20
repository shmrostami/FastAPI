from datetime import datetime, timedelta, timezone
from typing import Annotated
import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

load_dotenv(override=True)

from TodoApp.database import SessionLocal
from ..models import Users

router = APIRouter(prefix="/auth", tags=["auth"])

# import secrets
# print(secrets.token_hex(64))

SECRET_KEY = os.getenv("JWT_SECRET")
# print("The JWT_SECRET: ", SECRET_KEY)
if not SECRET_KEY:
    raise ValueError("JWT_SECRET environment variable is not set. ")
ALGORITHM = "HS256"

# bcrypt has a 72-byte limit; truncate to avoid ValueError
BCRYPT_MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:BCRYPT_MAX_PASSWORD_BYTES]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")


oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")


class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str


def get_db():
    db = None
    try:
        db = SessionLocal()
        yield db
    finally:
        if db is not None:
            db.close()


db_dependency = Annotated[Session, Depends(get_db)]


def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return None
    pwd_bytes = password.encode("utf-8")[:BCRYPT_MAX_PASSWORD_BYTES]
    if not bcrypt.checkpw(pwd_bytes, user.hashed_password.encode("utf-8")):
        return None
    return user


def create_access_token(
    username: str, user_id: int, role: str, expires_delta: timedelta | None = None
) -> str:
    encode = {"sub": username, "id": user_id, "role": role}
    if expires_delta is None:
        expires_delta = timedelta(minutes=20)
    expires = datetime.now(timezone.utc) + expires_delta
    encode["exp"] = int(expires.timestamp())  # JWT expects Unix timestamp
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: str = payload.get("role")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        return {"username": username, "id": user_id, "user_role": user_role}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        hashed_password=hash_password(create_user_request.password),
        is_active=True,
    )
    db.add(create_user_model)
    db.commit()
    # return create_user_model


@router.post("/token", response_model=Token)
async def login_for_access_token(
    db: db_dependency, form_data: OAuth2PasswordRequestForm = Depends()
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(
        user.username,
        user.id,
        user.role,
        expires_delta=timedelta(minutes=20),
    )
    return {"access_token": access_token, "token_type": "bearer"}
