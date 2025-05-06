"""Tests for generate_test_fixtures.py script."""

import os
import json
import tempfile
import pytest

from scripts.generate_test_fixtures import generate_fixtures, generate_hallucinations


@pytest.mark.unit
def test_generate_fixtures():
    """Test generate_fixtures function."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Generate fixtures
        generate_fixtures(temp_dir, count=5)
        
        # Check that the files were created
        assert os.path.exists(os.path.join(temp_dir, "documents.json"))
        assert os.path.exists(os.path.join(temp_dir, "users.json"))
        assert os.path.exists(os.path.join(temp_dir, "messages.json"))
        assert os.path.exists(os.path.join(temp_dir, "embedding_points.json"))
        
        # Check the content of the files
        with open(os.path.join(temp_dir, "documents.json"), "r") as f:
            documents = json.load(f)
            assert len(documents) == 5
            assert all(isinstance(doc, dict) for doc in documents)
            assert all("id" in doc for doc in documents)
            assert all("title" in doc for doc in documents)
            assert all("content" in doc for doc in documents)
        
        with open(os.path.join(temp_dir, "users.json"), "r") as f:
            users = json.load(f)
            assert len(users) == 5
            assert all(isinstance(user, dict) for user in users)
            assert all("id" in user for user in users)
            assert all("email" in user for user in users)
        
        with open(os.path.join(temp_dir, "messages.json"), "r") as f:
            messages = json.load(f)
            assert len(messages) == 5
            assert all(isinstance(message, dict) for message in messages)
            assert all("id" in message for message in messages)
            assert all("content" in message for message in messages)
        
        with open(os.path.join(temp_dir, "embedding_points.json"), "r") as f:
            embedding_points = json.load(f)
            assert len(embedding_points) == 5
            assert all(isinstance(point, dict) for point in embedding_points)
            assert all("id" in point for point in embedding_points)
            assert all("vector" in point for point in embedding_points)
            assert all(len(point["vector"]) == 768 for point in embedding_points)


@pytest.mark.unit
def test_generate_hallucinations():
    """Test generate_hallucinations function."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Generate hallucinations
        generate_hallucinations(temp_dir, count=5)
        
        # Check that the file was created
        assert os.path.exists(os.path.join(temp_dir, "hallucinations.json"))
        
        # Check the content of the file
        with open(os.path.join(temp_dir, "hallucinations.json"), "r") as f:
            hallucinations = json.load(f)
            assert len(hallucinations) == 5
            assert all(isinstance(hall, dict) for hall in hallucinations)
            assert all("id" in hall for hall in hallucinations)
            assert all("original_text" in hall for hall in hallucinations)
            assert all("hallucinated_text" in hall for hall in hallucinations)
            assert all("explanation" in hall for hall in hallucinations)
