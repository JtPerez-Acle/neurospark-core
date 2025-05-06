"""Database module for NeuroSpark Core.

This module contains database models and connections for Postgres 16.
"""

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
from src.database.connection import get_engine, create_database, get_session, get_session_sync
