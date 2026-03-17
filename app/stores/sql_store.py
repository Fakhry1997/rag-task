"""Stub — implementation in a later phase."""
from app.core.config import settings
from app.models.db_models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


class SQLStore:
    def get_session(self):
        return SessionLocal()
