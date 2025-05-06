"""Tests for database models."""

import datetime
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.database.models import (
    Base,
    Document,
    DocumentChunk,
    VectorEmbedding,
    User,
    UserInteraction,
    Lesson,
    LessonFeedback,
    AuditLog,
    MaintenanceLog,
)


@pytest.fixture
def engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create a new database session for testing."""
    with Session(engine) as session:
        yield session


def test_document_model(session):
    """Test the Document model."""
    # Create a document
    document = Document(
        title="Test Document",
        source_url="https://example.com/test",
        source_type="web",
        content="This is a test document.",
        metadata={"author": "Test Author", "tags": ["test", "document"]},
    )
    session.add(document)
    session.commit()

    # Query the document
    result = session.execute(select(Document)).scalar_one()

    # Check the document attributes
    assert result.id is not None
    assert result.title == "Test Document"
    assert result.source_url == "https://example.com/test"
    assert result.source_type == "web"
    assert result.content == "This is a test document."
    assert result.metadata == {"author": "Test Author", "tags": ["test", "document"]}
    assert result.created_at is not None
    assert result.updated_at is not None
    assert result.is_active is True


def test_document_chunk_model(session):
    """Test the DocumentChunk model."""
    # Create a document
    document = Document(
        title="Test Document",
        source_url="https://example.com/test",
        source_type="web",
        content="This is a test document.",
    )
    session.add(document)
    session.commit()

    # Create a document chunk
    chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        content="This is a test chunk.",
        metadata={"position": "start"},
    )
    session.add(chunk)
    session.commit()

    # Query the document chunk
    result = session.execute(select(DocumentChunk)).scalar_one()

    # Check the document chunk attributes
    assert result.id is not None
    assert result.document_id == document.id
    assert result.chunk_index == 0
    assert result.content == "This is a test chunk."
    assert result.metadata == {"position": "start"}
    assert result.created_at is not None
    assert result.is_active is True


def test_vector_embedding_model(session):
    """Test the VectorEmbedding model."""
    # Create a document
    document = Document(
        title="Test Document",
        source_url="https://example.com/test",
        source_type="web",
        content="This is a test document.",
    )
    session.add(document)
    session.commit()

    # Create a document chunk
    chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        content="This is a test chunk.",
    )
    session.add(chunk)
    session.commit()

    # Create a vector embedding
    embedding = VectorEmbedding(
        chunk_id=chunk.id,
        model_name="test-model",
        dimensions=3,
        vector=[0.1, 0.2, 0.3],
        metadata={"quality_score": 0.95},
    )
    session.add(embedding)
    session.commit()

    # Query the vector embedding
    result = session.execute(select(VectorEmbedding)).scalar_one()

    # Check the vector embedding attributes
    assert result.id is not None
    assert result.chunk_id == chunk.id
    assert result.model_name == "test-model"
    assert result.dimensions == 3
    assert result.vector == [0.1, 0.2, 0.3]
    assert result.metadata == {"quality_score": 0.95}
    assert result.created_at is not None


def test_user_model(session):
    """Test the User model."""
    # Create a user
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        user_preferences={"theme": "dark", "notifications": True},
    )
    session.add(user)
    session.commit()

    # Query the user
    result = session.execute(select(User)).scalar_one()

    # Check the user attributes
    assert result.id is not None
    assert result.username == "testuser"
    assert result.email == "test@example.com"
    assert result.full_name == "Test User"
    assert result.user_preferences == {"theme": "dark", "notifications": True}
    assert result.created_at is not None
    assert result.updated_at is not None
    assert result.is_active is True


def test_user_interaction_model(session):
    """Test the UserInteraction model."""
    # Create a user
    user = User(
        username="testuser",
        email="test@example.com",
    )
    session.add(user)
    session.commit()

    # Create a document
    document = Document(
        title="Test Document",
        source_url="https://example.com/test",
        source_type="web",
        content="This is a test document.",
    )
    session.add(document)
    session.commit()

    # Create a user interaction
    interaction = UserInteraction(
        user_id=user.id,
        document_id=document.id,
        interaction_type="view",
        interaction_metadata={"duration": 120, "completion": 0.8},
    )
    session.add(interaction)
    session.commit()

    # Query the user interaction
    result = session.execute(select(UserInteraction)).scalar_one()

    # Check the user interaction attributes
    assert result.id is not None
    assert result.user_id == user.id
    assert result.document_id == document.id
    assert result.interaction_type == "view"
    assert result.interaction_metadata == {"duration": 120, "completion": 0.8}
    assert result.created_at is not None


def test_lesson_model(session):
    """Test the Lesson model."""
    # Create a lesson
    lesson = Lesson(
        title="Test Lesson",
        content="This is a test lesson.",
        lesson_metadata={"difficulty": "beginner", "tags": ["test", "lesson"]},
    )
    session.add(lesson)
    session.commit()

    # Query the lesson
    result = session.execute(select(Lesson)).scalar_one()

    # Check the lesson attributes
    assert result.id is not None
    assert result.title == "Test Lesson"
    assert result.content == "This is a test lesson."
    assert result.lesson_metadata == {"difficulty": "beginner", "tags": ["test", "lesson"]}
    assert result.created_at is not None
    assert result.updated_at is not None
    assert result.is_active is True


def test_lesson_feedback_model(session):
    """Test the LessonFeedback model."""
    # Create a user
    user = User(
        username="testuser",
        email="test@example.com",
    )
    session.add(user)

    # Create a lesson
    lesson = Lesson(
        title="Test Lesson",
        content="This is a test lesson.",
    )
    session.add(lesson)
    session.commit()

    # Create lesson feedback
    feedback = LessonFeedback(
        user_id=user.id,
        lesson_id=lesson.id,
        rating=4,
        feedback_text="Good lesson!",
        feedback_metadata={"completion_time": 300},
    )
    session.add(feedback)
    session.commit()

    # Query the lesson feedback
    result = session.execute(select(LessonFeedback)).scalar_one()

    # Check the lesson feedback attributes
    assert result.id is not None
    assert result.user_id == user.id
    assert result.lesson_id == lesson.id
    assert result.rating == 4
    assert result.feedback_text == "Good lesson!"
    assert result.feedback_metadata == {"completion_time": 300}
    assert result.created_at is not None


def test_audit_log_model(session):
    """Test the AuditLog model."""
    # Create an audit log
    audit_log = AuditLog(
        agent="curator",
        action="document_fetch",
        status="success",
        log_details={"document_id": 123, "source": "example.com"},
    )
    session.add(audit_log)
    session.commit()

    # Query the audit log
    result = session.execute(select(AuditLog)).scalar_one()

    # Check the audit log attributes
    assert result.id is not None
    assert result.agent == "curator"
    assert result.action == "document_fetch"
    assert result.status == "success"
    assert result.log_details == {"document_id": 123, "source": "example.com"}
    assert result.created_at is not None


def test_maintenance_log_model(session):
    """Test the MaintenanceLog model."""
    # Create a maintenance log
    maintenance_log = MaintenanceLog(
        operation_type="vector_deduplication",
        status="success",
        affected_records=150,
        maintenance_details={"threshold": 0.95, "duration": 120},
    )
    session.add(maintenance_log)
    session.commit()

    # Query the maintenance log
    result = session.execute(select(MaintenanceLog)).scalar_one()

    # Check the maintenance log attributes
    assert result.id is not None
    assert result.operation_type == "vector_deduplication"
    assert result.status == "success"
    assert result.affected_records == 150
    assert result.maintenance_details == {"threshold": 0.95, "duration": 120}
    assert result.created_at is not None


def test_relationships(session):
    """Test the relationships between models."""
    # Create a user
    user = User(username="testuser", email="test@example.com")
    session.add(user)

    # Create a document
    document = Document(
        title="Test Document",
        source_url="https://example.com/test",
        source_type="web",
        content="This is a test document.",
    )
    session.add(document)
    session.commit()

    # Create document chunks
    chunk1 = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        content="This is the first chunk.",
    )
    chunk2 = DocumentChunk(
        document_id=document.id,
        chunk_index=1,
        content="This is the second chunk.",
    )
    session.add_all([chunk1, chunk2])
    session.commit()

    # Create vector embeddings
    embedding1 = VectorEmbedding(
        chunk_id=chunk1.id,
        model_name="test-model",
        dimensions=3,
        vector=[0.1, 0.2, 0.3],
    )
    embedding2 = VectorEmbedding(
        chunk_id=chunk2.id,
        model_name="test-model",
        dimensions=3,
        vector=[0.4, 0.5, 0.6],
    )
    session.add_all([embedding1, embedding2])

    # Create a user interaction
    interaction = UserInteraction(
        user_id=user.id,
        document_id=document.id,
        interaction_type="view",
    )
    session.add(interaction)
    session.commit()

    # Test document-chunk relationship
    document_result = session.execute(select(Document)).scalar_one()
    assert len(document_result.chunks) == 2
    assert document_result.chunks[0].content == "This is the first chunk."
    assert document_result.chunks[1].content == "This is the second chunk."

    # Test chunk-embedding relationship
    chunk_result = session.execute(select(DocumentChunk).where(DocumentChunk.id == chunk1.id)).scalar_one()
    assert len(chunk_result.embeddings) == 1
    assert chunk_result.embeddings[0].vector == [0.1, 0.2, 0.3]

    # Test user-interaction relationship
    user_result = session.execute(select(User)).scalar_one()
    assert len(user_result.interactions) == 1
    assert user_result.interactions[0].interaction_type == "view"

    # Test document-interaction relationship
    document_result = session.execute(select(Document)).scalar_one()
    assert len(document_result.interactions) == 1
    assert document_result.interactions[0].interaction_type == "view"
