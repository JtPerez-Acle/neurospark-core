"""Database models for NeuroSpark Core."""

import datetime
from typing import Dict, List, Optional, Any, Union

from sqlalchemy import ForeignKey, String, Boolean, Integer, DateTime, JSON, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )


class ActiveMixin:
    """Mixin for is_active flag."""

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Document(Base, TimestampMixin, ActiveMixin):
    """Document model for storing raw documents."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    doc_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)

    # Relationships
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    interactions: Mapped[List["UserInteraction"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Document(id={self.id!r}, title={self.title!r})"


class DocumentChunk(Base, TimestampMixin, ActiveMixin):
    """Document chunk model for storing document chunks."""

    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    chunk_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship(back_populates="chunks")
    embeddings: Mapped[List["VectorEmbedding"]] = relationship(
        back_populates="chunk", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"DocumentChunk(id={self.id!r}, document_id={self.document_id!r}, chunk_index={self.chunk_index!r})"


class VectorEmbedding(Base, TimestampMixin):
    """Vector embedding model for storing vector embeddings."""

    __tablename__ = "vector_embeddings"

    id: Mapped[int] = mapped_column(primary_key=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("document_chunks.id"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    vector: Mapped[List[float]] = mapped_column(JSON, nullable=False)
    embedding_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    chunk: Mapped["DocumentChunk"] = relationship(back_populates="embeddings")

    def __repr__(self) -> str:
        return f"VectorEmbedding(id={self.id!r}, chunk_id={self.chunk_id!r}, model_name={self.model_name!r})"


class User(Base, TimestampMixin, ActiveMixin):
    """User model for storing user information."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    user_preferences: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    interactions: Mapped[List["UserInteraction"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    lesson_feedback: Mapped[List["LessonFeedback"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r}, email={self.email!r})"


class UserInteraction(Base, TimestampMixin):
    """User interaction model for storing user interactions with documents."""

    __tablename__ = "user_interactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False)
    interaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    interaction_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="interactions")
    document: Mapped["Document"] = relationship(back_populates="interactions")

    def __repr__(self) -> str:
        return f"UserInteraction(id={self.id!r}, user_id={self.user_id!r}, document_id={self.document_id!r})"


class Lesson(Base, TimestampMixin, ActiveMixin):
    """Lesson model for storing lessons."""

    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    lesson_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    feedback: Mapped[List["LessonFeedback"]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Lesson(id={self.id!r}, title={self.title!r})"


class LessonFeedback(Base, TimestampMixin):
    """Lesson feedback model for storing user feedback on lessons."""

    __tablename__ = "lesson_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    feedback_text: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    feedback_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="lesson_feedback")
    lesson: Mapped["Lesson"] = relationship(back_populates="feedback")

    def __repr__(self) -> str:
        return f"LessonFeedback(id={self.id!r}, user_id={self.user_id!r}, lesson_id={self.lesson_id!r})"


class AuditLog(Base, TimestampMixin):
    """Audit log model for storing audit logs."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    agent: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    log_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"AuditLog(id={self.id!r}, agent={self.agent!r}, action={self.action!r})"


class MaintenanceLog(Base, TimestampMixin):
    """Maintenance log model for storing maintenance logs."""

    __tablename__ = "maintenance_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    operation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    affected_records: Mapped[int] = mapped_column(Integer, nullable=False)
    maintenance_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"MaintenanceLog(id={self.id!r}, operation_type={self.operation_type!r}, status={self.status!r})"
