"""Feedback management and analysis for agents.

This module provides feedback management and analysis capabilities for agents,
including feedback aggregation, analysis, and learning from feedback.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Type, Union

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session

from src.agents.enhanced_agent import EnhancedAgent
from src.agents.enhanced_message import FeedbackMessage

logger = logging.getLogger(__name__)

Base = declarative_base()


class Feedback(Base):
    """Feedback model for storing feedback in the database."""

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    sender_id = Column(String, nullable=False)
    recipient_id = Column(String, nullable=False)
    content_id = Column(String, nullable=True)
    message_id = Column(String, nullable=True)
    feedback_type = Column(String, nullable=False)
    feedback_data = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class FeedbackManager:
    """Manager for feedback recording, retrieval, and summarization."""

    def __init__(self, db_session: Session):
        """Initialize the feedback manager.

        Args:
            db_session: The database session to use.
        """
        self.db_session = db_session

    def record_feedback(
        self,
        sender_id: str,
        recipient_id: str,
        feedback_data: Dict[str, Any],
        content_id: Optional[str] = None,
        message_id: Optional[str] = None,
        feedback_type: str = "general",
    ) -> Feedback:
        """Record feedback in the database.

        Args:
            sender_id: The ID of the sender.
            recipient_id: The ID of the recipient.
            feedback_data: The feedback data.
            content_id: The ID of the content the feedback is about.
            message_id: The ID of the message the feedback is about.
            feedback_type: The type of feedback.

        Returns:
            The created feedback record.
        """
        feedback = Feedback(
            sender_id=sender_id,
            recipient_id=recipient_id,
            content_id=content_id,
            message_id=message_id,
            feedback_type=feedback_type,
            feedback_data=feedback_data,
            created_at=datetime.utcnow(),
        )

        self.db_session.add(feedback)
        self.db_session.commit()

        return feedback

    def get_feedback_for_recipient(
        self,
        recipient_id: str,
        feedback_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Feedback]:
        """Get feedback for a recipient.

        Args:
            recipient_id: The ID of the recipient.
            feedback_type: Optional filter for feedback type.
            limit: Maximum number of feedback records to return.

        Returns:
            List of feedback records.
        """
        query = self.db_session.query(Feedback).filter(Feedback.recipient_id == recipient_id)

        if feedback_type:
            query = query.filter(Feedback.feedback_type == feedback_type)

        return query.order_by(Feedback.created_at.desc()).limit(limit).all()

    def get_feedback_for_content(
        self,
        content_id: str,
        limit: int = 100,
    ) -> List[Feedback]:
        """Get feedback for a content item.

        Args:
            content_id: The ID of the content.
            limit: Maximum number of feedback records to return.

        Returns:
            List of feedback records.
        """
        return (
            self.db_session.query(Feedback)
            .filter(Feedback.content_id == content_id)
            .order_by(Feedback.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_feedback_for_message(
        self,
        message_id: str,
        limit: int = 100,
    ) -> List[Feedback]:
        """Get feedback for a message.

        Args:
            message_id: The ID of the message.
            limit: Maximum number of feedback records to return.

        Returns:
            List of feedback records.
        """
        return (
            self.db_session.query(Feedback)
            .filter(Feedback.message_id == message_id)
            .order_by(Feedback.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_feedback_summary(
        self,
        recipient_id: str,
        feedback_type: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get a summary of feedback for a recipient.

        Args:
            recipient_id: The ID of the recipient.
            feedback_type: Optional filter for feedback type.
            days: Number of days to include in the summary.

        Returns:
            Feedback summary.
        """
        # Get feedback for the recipient
        query = self.db_session.query(Feedback).filter(Feedback.recipient_id == recipient_id)

        if feedback_type:
            query = query.filter(Feedback.feedback_type == feedback_type)

        # Filter by date
        since_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Feedback.created_at >= since_date)

        # Get all matching feedback
        feedback_records = query.all()

        # Calculate summary statistics
        summary = {
            "recipient_id": recipient_id,
            "feedback_type": feedback_type,
            "days": days,
            "count": len(feedback_records),
            "average_scores": {},
            "common_suggestions": [],
            "improvement_areas": [],
        }

        # Extract scores and suggestions
        scores = {}
        suggestions = []

        for record in feedback_records:
            # Extract scores
            for key, value in record.feedback_data.items():
                if isinstance(value, (int, float)) and key != "timestamp":
                    if key not in scores:
                        scores[key] = []
                    scores[key].append(value)

            # Extract suggestions
            if "suggestions" in record.feedback_data:
                suggestions.extend(record.feedback_data["suggestions"])

        # Calculate average scores
        for key, values in scores.items():
            summary["average_scores"][key] = sum(values) / len(values) if values else 0

        # Find common suggestions
        suggestion_counts = {}
        for suggestion in suggestions:
            suggestion_counts[suggestion] = suggestion_counts.get(suggestion, 0) + 1

        # Sort suggestions by frequency
        sorted_suggestions = sorted(
            suggestion_counts.items(), key=lambda x: x[1], reverse=True
        )

        # Add top suggestions to summary
        summary["common_suggestions"] = [s[0] for s in sorted_suggestions[:5]]

        # Identify improvement areas (scores below 7.0)
        for key, avg in summary["average_scores"].items():
            if avg < 7.0:
                summary["improvement_areas"].append(key)

        return summary


class FeedbackAnalyzer:
    """Analyzer for feedback data."""

    def __init__(self, feedback_manager: FeedbackManager):
        """Initialize the feedback analyzer.

        Args:
            feedback_manager: The feedback manager to use.
        """
        self.feedback_manager = feedback_manager

    def analyze_agent_performance(
        self,
        agent_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Analyze an agent's performance based on feedback.

        Args:
            agent_id: The ID of the agent to analyze.
            days: Number of days to include in the analysis.

        Returns:
            Performance analysis.
        """
        # Get feedback summary
        summary = self.feedback_manager.get_feedback_summary(agent_id, days=days)

        # Perform additional analysis
        analysis = {
            "agent_id": agent_id,
            "days": days,
            "feedback_count": summary["count"],
            "performance_scores": summary["average_scores"],
            "strengths": [],
            "weaknesses": [],
            "improvement_suggestions": summary["common_suggestions"],
            "trend": "stable",
        }

        # Identify strengths and weaknesses
        for key, score in summary["average_scores"].items():
            if score >= 0.8:
                analysis["strengths"].append(key)
            elif score <= 0.6:
                analysis["weaknesses"].append(key)

        # TODO: Analyze trends over time

        return analysis

    def compare_agents(
        self,
        agent_ids: List[str],
        metric: str,
        days: int = 30,
    ) -> Dict[str, float]:
        """Compare multiple agents on a specific metric.

        Args:
            agent_ids: List of agent IDs to compare.
            metric: The metric to compare.
            days: Number of days to include in the comparison.

        Returns:
            Comparison results.
        """
        results = {}

        for agent_id in agent_ids:
            summary = self.feedback_manager.get_feedback_summary(agent_id, days=days)
            if metric in summary["average_scores"]:
                results[agent_id] = summary["average_scores"][metric]
            else:
                results[agent_id] = 0.0

        return results


class FeedbackAwareAgent:
    """Mixin for agents that learn from feedback."""

    def __init__(self, feedback_manager: FeedbackManager):
        """Initialize the feedback-aware agent.

        Args:
            feedback_manager: The feedback manager to use.
        """
        self.feedback_manager = feedback_manager
        self.feedback_analyzer = FeedbackAnalyzer(feedback_manager)
        self.feedback_history = []

    async def process_feedback(self, feedback: FeedbackMessage) -> None:
        """Process feedback and learn from it.

        Args:
            feedback: The feedback message to process.
        """
        # Extract feedback data
        about_message_id = feedback.payload.get("about_message_id")
        feedback_data = feedback.payload.get("feedback_data", {})

        # Record feedback
        self.feedback_manager.record_feedback(
            sender_id=feedback.sender,
            recipient_id=self.id,
            feedback_data=feedback_data,
            message_id=about_message_id,
        )

        # Add to history
        self.feedback_history.append({
            "sender": feedback.sender,
            "about_message_id": about_message_id,
            "feedback_data": feedback_data,
            "received_at": datetime.utcnow(),
        })

        # Learn from feedback
        await self.learn_from_feedback(feedback_data)

    async def learn_from_feedback(self, feedback_data: Dict[str, Any]) -> None:
        """Learn from feedback data.

        This method should be implemented by subclasses to learn from feedback.

        Args:
            feedback_data: The feedback data to learn from.
        """
        pass

    async def get_performance_analysis(self) -> Dict[str, Any]:
        """Get a performance analysis based on feedback.

        Returns:
            Performance analysis.
        """
        return self.feedback_analyzer.analyze_agent_performance(self.id)

    async def identify_improvement_areas(self) -> List[str]:
        """Identify areas for improvement based on feedback.

        Returns:
            List of improvement areas.
        """
        analysis = await self.get_performance_analysis()
        return analysis["weaknesses"]
