"""Integration tests for API module."""

import pytest
from fastapi import status

from src.database.models import User


@pytest.mark.integration
def test_health_endpoint(api_client):
    """Test health endpoint."""
    response = api_client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "ok"


@pytest.mark.integration
def test_user_endpoints(api_client, db_session):
    """Test user endpoints."""
    # Create a test user in the database
    user = User(
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
    )
    db_session.add(user)
    db_session.commit()
    
    # Get the user by ID
    response = api_client.get(f"/users/{user.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == "testuser"
    assert response.json()["email"] == "test@example.com"
    
    # Update the user
    update_data = {
        "first_name": "Updated",
        "last_name": "Name",
    }
    response = api_client.patch(f"/users/{user.id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["first_name"] == "Updated"
    assert response.json()["last_name"] == "Name"
    
    # Delete the user
    response = api_client.delete(f"/users/{user.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify the user is deleted
    response = api_client.get(f"/users/{user.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
