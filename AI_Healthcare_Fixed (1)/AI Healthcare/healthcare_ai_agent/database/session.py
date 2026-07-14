from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

if db_url.startswith("sqlite"):
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db() -> None:
    from models import models

    Base.metadata.create_all(bind=engine)
