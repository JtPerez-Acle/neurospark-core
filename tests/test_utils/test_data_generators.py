"""Tests for test data generators."""

import pytest
from datetime import datetime

from tests.test_utils.data_generators import (
    generate_random_string,
    generate_random_email,
    generate_random_date,
    generate_random_vector,
    generate_random_document,
    generate_random_documents,
    generate_random_user,
    generate_random_users,
    generate_random_message,
    generate_random_messages,
    generate_random_embedding_point,
    generate_random_embedding_points,
)


@pytest.mark.unit
def test_generate_random_string():
    """Test generate_random_string function."""
    # Test default length
    string1 = generate_random_string()
    assert isinstance(string1, str)
    assert len(string1) == 10
    
    # Test custom length
    string2 = generate_random_string(20)
    assert isinstance(string2, str)
    assert len(string2) == 20
    
    # Test uniqueness
    string3 = generate_random_string()
    assert string1 != string3


@pytest.mark.unit
def test_generate_random_email():
    """Test generate_random_email function."""
    email = generate_random_email()
    assert isinstance(email, str)
    assert "@" in email
    assert "." in email


@pytest.mark.unit
def test_generate_random_date():
    """Test generate_random_date function."""
    # Test default range
    date1 = generate_random_date()
    assert isinstance(date1, datetime)
    
    # Test custom range
    start_date = datetime(2010, 1, 1)
    end_date = datetime(2015, 12, 31)
    date2 = generate_random_date(start_date, end_date)
    assert isinstance(date2, datetime)
    assert start_date <= date2 <= end_date


@pytest.mark.unit
def test_generate_random_vector():
    """Test generate_random_vector function."""
    # Test default dimensions
    vector1 = generate_random_vector()
    assert isinstance(vector1, list)
    assert len(vector1) == 768
    assert all(isinstance(x, float) for x in vector1)
    
    # Test custom dimensions
    vector2 = generate_random_vector(512)
    assert isinstance(vector2, list)
    assert len(vector2) == 512
    assert all(isinstance(x, float) for x in vector2)


@pytest.mark.unit
def test_generate_random_document():
    """Test generate_random_document function."""
    doc = generate_random_document()
    assert isinstance(doc, dict)
    assert "id" in doc
    assert "title" in doc
    assert "content" in doc
    assert "created_at" in doc
    assert "metadata" in doc
    assert isinstance(doc["metadata"], dict)


@pytest.mark.unit
def test_generate_random_documents():
    """Test generate_random_documents function."""
    # Test default count
    docs1 = generate_random_documents()
    assert isinstance(docs1, list)
    assert len(docs1) == 10
    assert all(isinstance(doc, dict) for doc in docs1)
    
    # Test custom count
    docs2 = generate_random_documents(5)
    assert isinstance(docs2, list)
    assert len(docs2) == 5
    assert all(isinstance(doc, dict) for doc in docs2)


@pytest.mark.unit
def test_generate_random_user():
    """Test generate_random_user function."""
    user = generate_random_user()
    assert isinstance(user, dict)
    assert "id" in user
    assert "first_name" in user
    assert "last_name" in user
    assert "email" in user
    assert "created_at" in user


@pytest.mark.unit
def test_generate_random_users():
    """Test generate_random_users function."""
    # Test default count
    users1 = generate_random_users()
    assert isinstance(users1, list)
    assert len(users1) == 10
    assert all(isinstance(user, dict) for user in users1)
    
    # Test custom count
    users2 = generate_random_users(5)
    assert isinstance(users2, list)
    assert len(users2) == 5
    assert all(isinstance(user, dict) for user in users2)


@pytest.mark.unit
def test_generate_random_message():
    """Test generate_random_message function."""
    message = generate_random_message()
    assert isinstance(message, dict)
    assert "id" in message
    assert "content" in message
    assert "created_at" in message
    assert "metadata" in message
    assert isinstance(message["metadata"], dict)


@pytest.mark.unit
def test_generate_random_messages():
    """Test generate_random_messages function."""
    # Test default count
    messages1 = generate_random_messages()
    assert isinstance(messages1, list)
    assert len(messages1) == 10
    assert all(isinstance(message, dict) for message in messages1)
    
    # Test custom count
    messages2 = generate_random_messages(5)
    assert isinstance(messages2, list)
    assert len(messages2) == 5
    assert all(isinstance(message, dict) for message in messages2)


@pytest.mark.unit
def test_generate_random_embedding_point():
    """Test generate_random_embedding_point function."""
    # Test default dimensions
    point1 = generate_random_embedding_point()
    assert isinstance(point1, dict)
    assert "id" in point1
    assert "vector" in point1
    assert "payload" in point1
    assert len(point1["vector"]) == 768
    
    # Test custom dimensions
    point2 = generate_random_embedding_point(512)
    assert isinstance(point2, dict)
    assert "id" in point2
    assert "vector" in point2
    assert "payload" in point2
    assert len(point2["vector"]) == 512


@pytest.mark.unit
def test_generate_random_embedding_points():
    """Test generate_random_embedding_points function."""
    # Test default count and dimensions
    points1 = generate_random_embedding_points()
    assert isinstance(points1, list)
    assert len(points1) == 10
    assert all(isinstance(point, dict) for point in points1)
    assert all(len(point["vector"]) == 768 for point in points1)
    
    # Test custom count and dimensions
    points2 = generate_random_embedding_points(5, 512)
    assert isinstance(points2, list)
    assert len(points2) == 5
    assert all(isinstance(point, dict) for point in points2)
    assert all(len(point["vector"]) == 512 for point in points2)
