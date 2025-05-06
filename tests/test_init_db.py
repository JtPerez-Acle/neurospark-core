"""Tests for database initialization script."""

import pytest
from unittest.mock import patch, MagicMock

from scripts.init_db import init_db


@patch("scripts.init_db.command")
@patch("scripts.init_db.Config")
@patch("scripts.init_db.get_engine")
@patch("scripts.init_db.Base")
def test_init_db_create_tables_only(mock_base, mock_get_engine, mock_config, mock_command):
    """Test init_db function with create_tables=True and stamp_head=False."""
    # Setup
    mock_engine = MagicMock()
    mock_get_engine.return_value = mock_engine
    
    # Execute
    init_db(create_tables=True, stamp_head=False)
    
    # Assert
    mock_get_engine.assert_called_once()
    mock_base.metadata.create_all.assert_called_once_with(mock_engine)
    mock_config.assert_not_called()
    mock_command.stamp.assert_not_called()


@patch("scripts.init_db.command")
@patch("scripts.init_db.Config")
@patch("scripts.init_db.get_engine")
@patch("scripts.init_db.Base")
def test_init_db_stamp_head_only(mock_base, mock_get_engine, mock_config, mock_command):
    """Test init_db function with create_tables=False and stamp_head=True."""
    # Setup
    mock_alembic_cfg = MagicMock()
    mock_config.return_value = mock_alembic_cfg
    
    # Execute
    init_db(create_tables=False, stamp_head=True)
    
    # Assert
    mock_get_engine.assert_not_called()
    mock_base.metadata.create_all.assert_not_called()
    mock_config.assert_called_once()
    mock_command.stamp.assert_called_once_with(mock_alembic_cfg, "head")


@patch("scripts.init_db.command")
@patch("scripts.init_db.Config")
@patch("scripts.init_db.get_engine")
@patch("scripts.init_db.Base")
def test_init_db_both_options(mock_base, mock_get_engine, mock_config, mock_command):
    """Test init_db function with create_tables=True and stamp_head=True."""
    # Setup
    mock_engine = MagicMock()
    mock_get_engine.return_value = mock_engine
    
    mock_alembic_cfg = MagicMock()
    mock_config.return_value = mock_alembic_cfg
    
    # Execute
    init_db(create_tables=True, stamp_head=True)
    
    # Assert
    mock_get_engine.assert_called_once()
    mock_base.metadata.create_all.assert_called_once_with(mock_engine)
    mock_config.assert_called_once()
    mock_command.stamp.assert_called_once_with(mock_alembic_cfg, "head")


@patch("scripts.init_db.command")
@patch("scripts.init_db.Config")
@patch("scripts.init_db.get_engine")
@patch("scripts.init_db.Base")
def test_init_db_no_options(mock_base, mock_get_engine, mock_config, mock_command):
    """Test init_db function with create_tables=False and stamp_head=False."""
    # Execute
    init_db(create_tables=False, stamp_head=False)
    
    # Assert
    mock_get_engine.assert_not_called()
    mock_base.metadata.create_all.assert_not_called()
    mock_config.assert_not_called()
    mock_command.stamp.assert_not_called()
