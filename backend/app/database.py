"""Database connection and session management module.

This module sets up SQLAlchemy connection pooling to PostgreSQL, provides
a factory for creating database sessions, and includes health check helpers.
"""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings


@lru_cache
def get_engine():
    """Create and cache the synchronous PostgreSQL engine.

    'pool_pre_ping=True' checks if connections in the pool are still alive
    before using them, preventing stale connection errors.
    """
    return create_engine(get_settings().database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Create and cache the SQLAlchemy sessionmaker factory.

    Configured with autoflush=False and autocommit=False to ensure explicit,
    safe transaction management across repositories.
    """
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def get_database_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session for an HTTP request.

    The session is automatically closed in the 'finally' block when the
    request finishes, preventing connection leaks.
    """
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def check_database_connection() -> bool:
    """Execute a lightweight SQL query (SELECT 1) to test database readiness.

    Used by the /health/database endpoint to confirm PostgreSQL is operational.
    """
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except (RuntimeError, SQLAlchemyError):
        return False

    return True
