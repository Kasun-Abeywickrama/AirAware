"""Database engine, session, and readiness helpers."""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings


@lru_cache
def get_engine():
    """Create the shared synchronous PostgreSQL engine."""
    return create_engine(get_settings().database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Create the shared session factory for future repositories."""
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def get_database_session() -> Generator[Session, None, None]:
    """Provide one database session and close it after use."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def check_database_connection() -> bool:
    """Return whether PostgreSQL accepts a lightweight query."""
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except (RuntimeError, SQLAlchemyError):
        return False

    return True
