from sqlalchemy.orm import Session
from models.models import User
from models.schemas import UserCreate
from services.auth import get_password_hash
from database.session import SessionLocal


def create_user(user_data: UserCreate) -> User:
    with SessionLocal() as db:
        existing = db.query(User).filter((User.username == user_data.username) | (User.email == user_data.email)).first()
        if existing:
            raise ValueError('User with this username or email already exists')
        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            role=user_data.role,
            hashed_password=get_password_hash(user_data.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
