"""Integration tests for database module."""

import pytest
from sqlalchemy import text

from src.database.models import User


@pytest.mark.integration
def test_database_connection(db_engine):
    """Test database connection."""
    # Execute a simple query
    with db_engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


@pytest.mark.integration
def test_user_model_crud(db_session):
    """Test CRUD operations for User model."""
    # Create a user
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()

    # Read the user
    user_id = user.id
    retrieved_user = db_session.query(User).filter(User.id == user_id).first()
    assert retrieved_user is not None
    assert retrieved_user.username == "testuser"
    assert retrieved_user.email == "test@example.com"
    assert retrieved_user.full_name == "Test User"

    # Update the user
    retrieved_user.full_name = "Updated User"
    db_session.commit()

    # Verify the update
    updated_user = db_session.query(User).filter(User.id == user_id).first()
    assert updated_user.full_name == "Updated User"

    # Delete the user
    db_session.delete(updated_user)
    db_session.commit()

    # Verify the deletion
    deleted_user = db_session.query(User).filter(User.id == user_id).first()
    assert deleted_user is None
