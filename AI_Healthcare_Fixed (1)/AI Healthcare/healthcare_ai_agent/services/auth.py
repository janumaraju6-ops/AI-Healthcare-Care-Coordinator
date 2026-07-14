from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from config import settings
from database.session import SessionLocal
from models.models import User
from models.schemas import TokenData

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl='/api/auth/login', auto_error=False)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def authenticate_user(username: str, password: str) -> Optional[User]:
    with SessionLocal() as db:
        user = get_user_by_username(db, username)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get('sub')
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    with SessionLocal() as db:
        user = get_user_by_username(db, token_data.username)
        if user is None:
            raise credentials_exception
        return user


def get_current_user_optional(token: str | None = Depends(oauth2_scheme_optional)):
    if not token:
        return SimpleNamespace(
            id='guest',
            username='guest',
            email='guest@example.com',
            full_name='Guest User',
            role='patient',
        )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get('sub')
        if username is None:
            return SimpleNamespace(
                id='guest',
                username='guest',
                email='guest@example.com',
                full_name='Guest User',
                role='patient',
            )
        with SessionLocal() as db:
            user = get_user_by_username(db, username)
            if user is not None:
                return user
    except JWTError:
        pass

    return SimpleNamespace(
        id='guest',
        username='guest',
        email='guest@example.com',
        full_name='Guest User',
        role='patient',
    )
