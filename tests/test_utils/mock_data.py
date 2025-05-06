"""Mock data for NeuroSpark Core tests."""

from datetime import datetime, timezone
from typing import Dict, List, Any

# Sample documents
SAMPLE_DOCUMENTS = [
    {
        "id": "doc-001",
        "title": "Introduction to Machine Learning",
        "content": "Machine learning is a branch of artificial intelligence that focuses on building systems that learn from data.",
        "created_at": datetime(2023, 1, 1, tzinfo=timezone.utc).isoformat(),
        "metadata": {
            "source": "web",
            "author": "John Doe",
            "tags": ["machine learning", "ai", "introduction"],
        },
    },
    {
        "id": "doc-002",
        "title": "Deep Learning Fundamentals",
        "content": "Deep learning is a subset of machine learning that uses neural networks with many layers.",
        "created_at": datetime(2023, 1, 2, tzinfo=timezone.utc).isoformat(),
        "metadata": {
            "source": "book",
            "author": "Jane Smith",
            "tags": ["deep learning", "neural networks", "ai"],
        },
    },
    {
        "id": "doc-003",
        "title": "Natural Language Processing",
        "content": "Natural Language Processing (NLP) is a field of AI that focuses on the interaction between computers and human language.",
        "created_at": datetime(2023, 1, 3, tzinfo=timezone.utc).isoformat(),
        "metadata": {
            "source": "article",
            "author": "Bob Johnson",
            "tags": ["nlp", "ai", "language"],
        },
    },
]

# Sample users
SAMPLE_USERS = [
    {
        "id": "user-001",
        "first_name": "Alice",
        "last_name": "Anderson",
        "email": "alice@example.com",
        "created_at": datetime(2023, 1, 1, tzinfo=timezone.utc).isoformat(),
    },
    {
        "id": "user-002",
        "first_name": "Bob",
        "last_name": "Brown",
        "email": "bob@example.com",
        "created_at": datetime(2023, 1, 2, tzinfo=timezone.utc).isoformat(),
    },
    {
        "id": "user-003",
        "first_name": "Charlie",
        "last_name": "Clark",
        "email": "charlie@example.com",
        "created_at": datetime(2023, 1, 3, tzinfo=timezone.utc).isoformat(),
    },
]

# Sample messages
SAMPLE_MESSAGES = [
    {
        "id": "msg-001",
        "content": "Hello, how can I help you today?",
        "created_at": datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
        "metadata": {
            "source": "agent",
            "tags": ["greeting"],
        },
    },
    {
        "id": "msg-002",
        "content": "I'd like to learn about machine learning.",
        "created_at": datetime(2023, 1, 1, 10, 1, 0, tzinfo=timezone.utc).isoformat(),
        "metadata": {
            "source": "user",
            "tags": ["question"],
        },
    },
    {
        "id": "msg-003",
        "content": "Machine learning is a branch of artificial intelligence that focuses on building systems that learn from data.",
        "created_at": datetime(2023, 1, 1, 10, 2, 0, tzinfo=timezone.utc).isoformat(),
        "metadata": {
            "source": "agent",
            "tags": ["answer"],
        },
    },
]

# Sample embedding points
SAMPLE_EMBEDDING_POINTS = [
    {
        "id": "emb-001",
        "vector": [0.1, 0.2, 0.3, 0.4, 0.5] * 153 + [0.1, 0.2, 0.3],  # 768 dimensions
        "payload": {
            "text": "Machine learning is a branch of artificial intelligence.",
            "metadata": {
                "source": "document",
                "created_at": datetime(2023, 1, 1, tzinfo=timezone.utc).isoformat(),
            },
        },
    },
    {
        "id": "emb-002",
        "vector": [0.2, 0.3, 0.4, 0.5, 0.6] * 153 + [0.2, 0.3, 0.4],  # 768 dimensions
        "payload": {
            "text": "Deep learning uses neural networks with many layers.",
            "metadata": {
                "source": "document",
                "created_at": datetime(2023, 1, 2, tzinfo=timezone.utc).isoformat(),
            },
        },
    },
    {
        "id": "emb-003",
        "vector": [0.3, 0.4, 0.5, 0.6, 0.7] * 153 + [0.3, 0.4, 0.5],  # 768 dimensions
        "payload": {
            "text": "Natural Language Processing focuses on interaction between computers and human language.",
            "metadata": {
                "source": "document",
                "created_at": datetime(2023, 1, 3, tzinfo=timezone.utc).isoformat(),
            },
        },
    },
]

# Sample hallucinations for reviewer testing
SAMPLE_HALLUCINATIONS = [
    {
        "id": "hall-001",
        "original_text": "Machine learning was invented by Arthur Samuel in 1959.",
        "hallucinated_text": "Machine learning was invented by John McCarthy in 1955.",
        "explanation": "Arthur Samuel coined the term 'machine learning' in 1959, but John McCarthy did not invent it in 1955.",
    },
    {
        "id": "hall-002",
        "original_text": "Deep learning neural networks typically have 3-10 layers.",
        "hallucinated_text": "Deep learning neural networks typically have 100-1000 layers.",
        "explanation": "Most practical deep learning models have between 3-100 layers, not 100-1000.",
    },
    {
        "id": "hall-003",
        "original_text": "Python was created by Guido van Rossum in 1991.",
        "hallucinated_text": "Python was created by Guido van Rossum in 1985.",
        "explanation": "Python was first released in 1991, not 1985.",
    },
]
