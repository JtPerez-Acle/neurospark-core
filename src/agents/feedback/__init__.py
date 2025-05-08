"""Feedback module for NeuroSpark Core.

This module provides feedback aggregation and analysis capabilities for agents.
"""

from src.agents.feedback.manager import FeedbackManager, FeedbackAnalyzer, FeedbackAwareAgent

__all__ = [
    "FeedbackManager",
    "FeedbackAnalyzer",
    "FeedbackAwareAgent",
]
