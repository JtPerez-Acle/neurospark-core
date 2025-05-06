"""Tests for database connection module."""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from sqlalchemy import Engine

from src.database.connection import get_engine, create_database, get_session, get_session_sync


@patch("src.database.connection.create_engine")
@patch("src.database.connection.settings")
def test_get_engine(mock_settings, mock_create_engine):
    """Test get_engine function."""
    # Setup
    mock_engine = MagicMock(spec=Engine)
    mock_create_engine.return_value = mock_engine
    mock_settings.database.url = "postgresql://user:pass@localhost/test"
    mock_settings.environment = "development"
    
    # Execute
    engine = get_engine()
    
    # Assert
    assert engine == mock_engine
    mock_create_engine.assert_called_once_with(
        "postgresql://user:pass@localhost/test",
        echo=True,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


@patch("src.database.connection.get_engine")
@patch("src.database.connection.Base")
def test_create_database(mock_base, mock_get_engine):
    """Test create_database function."""
    # Setup
    mock_engine = MagicMock(spec=Engine)
    mock_get_engine.return_value = mock_engine
    
    # Execute
    create_database()
    
    # Assert
    mock_get_engine.assert_called_once()
    mock_base.metadata.create_all.assert_called_once_with(mock_engine)


@patch("src.database.connection.get_engine")
@patch("src.database.connection.sessionmaker")
def test_get_session(mock_sessionmaker, mock_get_engine):
    """Test get_session function."""
    # Setup
    mock_engine = MagicMock(spec=Engine)
    mock_get_engine.return_value = mock_engine
    
    mock_session_factory = MagicMock()
    mock_session = MagicMock(spec=Session)
    mock_session_factory.return_value = mock_session
    mock_sessionmaker.return_value = mock_session_factory
    
    # Execute
    session_generator = get_session()
    session = next(session_generator)
    
    # Assert
    assert session == mock_session
    mock_get_engine.assert_called_once()
    mock_sessionmaker.assert_called_once_with(
        autocommit=False, autoflush=False, bind=mock_engine
    )
    mock_session_factory.assert_called_once()
    
    # Test session close on generator exit
    try:
        next(session_generator)
    except StopIteration:
        pass
    
    mock_session.close.assert_called_once()


@patch("src.database.connection.get_engine")
@patch("src.database.connection.sessionmaker")
def test_get_session_sync(mock_sessionmaker, mock_get_engine):
    """Test get_session_sync function."""
    # Setup
    mock_engine = MagicMock(spec=Engine)
    mock_get_engine.return_value = mock_engine
    
    mock_session_factory = MagicMock()
    mock_session = MagicMock(spec=Session)
    mock_session_factory.return_value = mock_session
    mock_sessionmaker.return_value = mock_session_factory
    
    # Execute
    session = get_session_sync()
    
    # Assert
    assert session == mock_session
    mock_get_engine.assert_called_once()
    mock_sessionmaker.assert_called_once_with(
        autocommit=False, autoflush=False, bind=mock_engine
    )
    mock_session_factory.assert_called_once()
