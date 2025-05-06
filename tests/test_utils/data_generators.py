"""Test data generators for NeuroSpark Core tests."""

import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple

import numpy as np


def generate_random_string(length: int = 10) -> str:
    """Generate a random string of fixed length.
    
    Args:
        length: The length of the string to generate.
        
    Returns:
        A random string.
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_email() -> str:
    """Generate a random email address.
    
    Returns:
        A random email address.
    """
    domains = ["example.com", "test.com", "fake.org", "mock.io"]
    username = generate_random_string(8).lower()
    domain = random.choice(domains)
    return f"{username}@{domain}"


def generate_random_date(
    start_date: datetime = datetime(2020, 1, 1),
    end_date: datetime = datetime.now(),
) -> datetime:
    """Generate a random date between start_date and end_date.
    
    Args:
        start_date: The start date.
        end_date: The end date.
        
    Returns:
        A random date between start_date and end_date.
    """
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)


def generate_random_vector(dimensions: int = 768) -> List[float]:
    """Generate a random vector of fixed dimensions.
    
    Args:
        dimensions: The dimensions of the vector.
        
    Returns:
        A random vector.
    """
    vector = np.random.randn(dimensions).tolist()
    return vector


def generate_random_document() -> Dict[str, Any]:
    """Generate a random document.
    
    Returns:
        A random document.
    """
    doc_id = str(uuid.uuid4())
    title = f"Document {generate_random_string(5)}"
    content = " ".join([generate_random_string(8) for _ in range(50)])
    created_at = generate_random_date()
    
    return {
        "id": doc_id,
        "title": title,
        "content": content,
        "created_at": created_at.isoformat(),
        "metadata": {
            "source": random.choice(["web", "pdf", "book", "article"]),
            "author": generate_random_string(10),
            "tags": [generate_random_string(5) for _ in range(3)],
        },
    }


def generate_random_documents(count: int = 10) -> List[Dict[str, Any]]:
    """Generate a list of random documents.
    
    Args:
        count: The number of documents to generate.
        
    Returns:
        A list of random documents.
    """
    return [generate_random_document() for _ in range(count)]


def generate_random_user() -> Dict[str, Any]:
    """Generate a random user.
    
    Returns:
        A random user.
    """
    user_id = str(uuid.uuid4())
    first_name = generate_random_string(8)
    last_name = generate_random_string(10)
    email = generate_random_email()
    
    return {
        "id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "created_at": generate_random_date().isoformat(),
    }


def generate_random_users(count: int = 10) -> List[Dict[str, Any]]:
    """Generate a list of random users.
    
    Args:
        count: The number of users to generate.
        
    Returns:
        A list of random users.
    """
    return [generate_random_user() for _ in range(count)]


def generate_random_message() -> Dict[str, Any]:
    """Generate a random message.
    
    Returns:
        A random message.
    """
    message_id = str(uuid.uuid4())
    content = " ".join([generate_random_string(8) for _ in range(10)])
    
    return {
        "id": message_id,
        "content": content,
        "created_at": generate_random_date().isoformat(),
        "metadata": {
            "source": random.choice(["user", "agent", "system"]),
            "tags": [generate_random_string(5) for _ in range(2)],
        },
    }


def generate_random_messages(count: int = 10) -> List[Dict[str, Any]]:
    """Generate a list of random messages.
    
    Args:
        count: The number of messages to generate.
        
    Returns:
        A list of random messages.
    """
    return [generate_random_message() for _ in range(count)]


def generate_random_embedding_point(dimensions: int = 768) -> Dict[str, Any]:
    """Generate a random embedding point for vector database.
    
    Args:
        dimensions: The dimensions of the vector.
        
    Returns:
        A random embedding point.
    """
    point_id = str(uuid.uuid4())
    vector = generate_random_vector(dimensions)
    
    return {
        "id": point_id,
        "vector": vector,
        "payload": {
            "text": " ".join([generate_random_string(8) for _ in range(10)]),
            "metadata": {
                "source": random.choice(["document", "query", "message"]),
                "created_at": generate_random_date().isoformat(),
            },
        },
    }


def generate_random_embedding_points(
    count: int = 10, dimensions: int = 768
) -> List[Dict[str, Any]]:
    """Generate a list of random embedding points.
    
    Args:
        count: The number of embedding points to generate.
        dimensions: The dimensions of the vectors.
        
    Returns:
        A list of random embedding points.
    """
    return [generate_random_embedding_point(dimensions) for _ in range(count)]
