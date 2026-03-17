from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.ingestion.excel_parser import StructuredRow
from app.models.db_models import Base, ProductSpec


def _ensure_data_dir() -> None:
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)


engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    _ensure_data_dir()
    Base.metadata.create_all(bind=engine)


class SQLStore:
    def insert_rows(
        self,
        rows: list[StructuredRow],
        client_id: str,
        source_file: str,
    ) -> int:
        """Persist structured rows; returns count inserted."""
        with SessionLocal() as session:
            objects = [
                ProductSpec(
                    client_id=client_id,
                    source_file=source_file,
                    product_name=row.product_name,
                    region=row.region,
                    parameter=row.parameter,
                    numeric_value=row.numeric_value,
                    unit=row.unit,
                    limit_type=row.limit_type,
                    notes=row.notes,
                )
                for row in rows
            ]
            session.add_all(objects)
            session.commit()
        return len(objects)

    def query_by_client(self, client_id: str) -> list[ProductSpec]:
        """Return all rows for a client. Always scoped by client_id."""
        with SessionLocal() as session:
            return (
                session.query(ProductSpec)
                .filter(ProductSpec.client_id == client_id)
                .all()
            )

    def get_session(self) -> Session:
        """Raw session for use in retriever SQL generation."""
        return SessionLocal()
