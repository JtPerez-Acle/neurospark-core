"""Database connection module for NeuroSpark Core."""

import logging
from typing import Generator

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session, sessionmaker

from src.common.config import settings
from src.database.models import Base

logger = logging.getLogger(__name__)


def get_engine() -> Engine:
    """Get a SQLAlchemy engine instance.

    Returns:
        Engine: A SQLAlchemy engine instance.
    """
    import os

    # Check for environment variables first (highest priority)
    host = os.environ.get("POSTGRES_HOST")
    port = os.environ.get("POSTGRES_PORT")
    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")
    db = os.environ.get("POSTGRES_DB")

    # If environment variables are set, use them
    if host and port and user and password and db:
        db_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
        logger.info("Using database URL from environment variables")
    else:
        # Otherwise use the settings
        db_url = settings.database.url

    logger.info("Connecting to database at: %s", db_url)

    return create_engine(
        db_url,
        echo=settings.environment == "development",
        pool_pre_ping=True,
        pool_recycle=3600,
    )


def create_database() -> None:
    """Create all database tables.

    This function creates all tables defined in the models module.
    """
    logger.info("Creating database tables")
    engine = get_engine()
    try:
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def get_session() -> Generator[Session, None, None]:
    """Get a SQLAlchemy session.

    Yields:
        Session: A SQLAlchemy session.
    """
    engine = get_engine()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def get_session_sync() -> Session:
    """Get a SQLAlchemy session synchronously.

    Returns:
        Session: A SQLAlchemy session.
    """
    engine = get_engine()
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return session_factory()
