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
    logger.info("Creating database engine with URL: %s", settings.database.url)
    return create_engine(
        settings.database.url,
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
    Base.metadata.create_all(engine)
    logger.info("Database tables created successfully")


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
