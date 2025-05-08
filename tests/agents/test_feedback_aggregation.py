"""Tests for the feedback aggregation system.

This module contains tests for the feedback aggregation system, including
feedback recording, retrieval, summarization, and analysis.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.agents.feedback.manager import Feedback, FeedbackManager, FeedbackAnalyzer, FeedbackAwareAgent


class MockSession:
    """Mock SQLAlchemy session for testing."""
    
    def __init__(self):
        self.added = []
        self.committed = False
        self.closed = False
        self.query_results = []
    
    def add(self, obj):
        """Add an object to the session."""
        self.added.append(obj)
    
    def commit(self):
        """Commit the session."""
        self.committed = True
    
    def close(self):
        """Close the session."""
        self.closed = True
    
    def query(self, cls):
        """Query the session."""
        return MockQuery(self.query_results)


class MockQuery:
    """Mock SQLAlchemy query for testing."""
    
    def __init__(self, results):
        self.results = results
        self.filters = []
        self.order_by_clause = None
        self.limit_value = None
    
    def filter(self, condition):
        """Add a filter to the query."""
        self.filters.append(condition)
        return self
    
    def order_by(self, clause):
        """Add an order by clause to the query."""
        self.order_by_clause = clause
        return self
    
    def limit(self, value):
        """Add a limit to the query."""
        self.limit_value = value
        return self
    
    def all(self):
        """Execute the query and return all results."""
        return self.results


@pytest.fixture
def mock_session():
    """Create a mock SQLAlchemy session."""
    return MockSession()


@pytest.fixture
def feedback_manager(mock_session):
    """Create a feedback manager with a mock session."""
    return FeedbackManager(mock_session)


@pytest.fixture
def feedback_analyzer(feedback_manager):
    """Create a feedback analyzer with a mock feedback manager."""
    return FeedbackAnalyzer(feedback_manager)


def test_record_feedback(feedback_manager):
    """Test recording feedback."""
    # Setup
    sender_id = "sender-agent"
    recipient_id = "recipient-agent"
    feedback_data = {
        "quality": 8,
        "relevance": 9,
        "suggestions": ["Improve clarity", "Add more examples"],
    }
    
    # Execute
    feedback = feedback_manager.record_feedback(
        sender_id=sender_id,
        recipient_id=recipient_id,
        feedback_data=feedback_data,
    )
    
    # Verify
    assert len(feedback_manager.db_session.added) == 1
    assert feedback_manager.db_session.committed
    
    recorded_feedback = feedback_manager.db_session.added[0]
    assert recorded_feedback.sender_id == sender_id
    assert recorded_feedback.recipient_id == recipient_id
    assert recorded_feedback.feedback_data == feedback_data
    assert recorded_feedback.feedback_type == "general"


def test_get_feedback_for_recipient(feedback_manager):
    """Test getting feedback for a recipient."""
    # Setup
    recipient_id = "recipient-agent"
    mock_feedback = [
        Feedback(
            id=1,
            sender_id="sender-agent-1",
            recipient_id=recipient_id,
            feedback_type="general",
            feedback_data={"quality": 8},
            created_at=datetime.utcnow(),
        ),
        Feedback(
            id=2,
            sender_id="sender-agent-2",
            recipient_id=recipient_id,
            feedback_type="general",
            feedback_data={"quality": 7},
            created_at=datetime.utcnow(),
        ),
    ]
    feedback_manager.db_session.query_results = mock_feedback
    
    # Execute
    results = feedback_manager.get_feedback_for_recipient(recipient_id)
    
    # Verify
    assert results == mock_feedback


def test_get_feedback_summary(feedback_manager):
    """Test getting a feedback summary."""
    # Setup
    recipient_id = "recipient-agent"
    mock_feedback = [
        Feedback(
            id=1,
            sender_id="sender-agent-1",
            recipient_id=recipient_id,
            feedback_type="general",
            feedback_data={
                "quality": 8,
                "relevance": 9,
                "suggestions": ["Improve clarity"],
            },
            created_at=datetime.utcnow(),
        ),
        Feedback(
            id=2,
            sender_id="sender-agent-2",
            recipient_id=recipient_id,
            feedback_type="general",
            feedback_data={
                "quality": 6,
                "relevance": 7,
                "suggestions": ["Add more examples"],
            },
            created_at=datetime.utcnow(),
        ),
        Feedback(
            id=3,
            sender_id="sender-agent-3",
            recipient_id=recipient_id,
            feedback_type="general",
            feedback_data={
                "quality": 5,
                "relevance": 8,
                "suggestions": ["Improve clarity", "Fix typos"],
            },
            created_at=datetime.utcnow(),
        ),
    ]
    feedback_manager.db_session.query_results = mock_feedback
    
    # Execute
    summary = feedback_manager.get_feedback_summary(recipient_id)
    
    # Verify
    assert summary["recipient_id"] == recipient_id
    assert summary["count"] == 3
    assert "quality" in summary["average_scores"]
    assert "relevance" in summary["average_scores"]
    assert summary["average_scores"]["quality"] == (8 + 6 + 5) / 3
    assert summary["average_scores"]["relevance"] == (9 + 7 + 8) / 3
    assert "Improve clarity" in summary["common_suggestions"]
    assert "quality" in summary["improvement_areas"]  # Average is 6.33, which is < 0.7


def test_analyze_agent_performance(feedback_analyzer):
    """Test analyzing agent performance."""
    # Setup
    agent_id = "agent-1"
    
    # Mock the get_feedback_summary method
    feedback_analyzer.feedback_manager.get_feedback_summary = MagicMock(return_value={
        "recipient_id": agent_id,
        "count": 10,
        "average_scores": {
            "quality": 0.85,
            "relevance": 0.9,
            "accuracy": 0.75,
            "clarity": 0.6,
        },
        "common_suggestions": [
            "Improve clarity",
            "Add more examples",
            "Fix typos",
        ],
        "improvement_areas": ["clarity"],
    })
    
    # Execute
    analysis = feedback_analyzer.analyze_agent_performance(agent_id)
    
    # Verify
    assert analysis["agent_id"] == agent_id
    assert analysis["feedback_count"] == 10
    assert "quality" in analysis["strengths"]
    assert "relevance" in analysis["strengths"]
    assert "clarity" in analysis["weaknesses"]
    assert "Improve clarity" in analysis["improvement_suggestions"]


def test_compare_agents(feedback_analyzer):
    """Test comparing agents."""
    # Setup
    agent_ids = ["agent-1", "agent-2", "agent-3"]
    metric = "quality"
    
    # Mock the get_feedback_summary method
    def mock_get_feedback_summary(agent_id, days=30):
        summaries = {
            "agent-1": {"average_scores": {"quality": 0.85}},
            "agent-2": {"average_scores": {"quality": 0.9}},
            "agent-3": {"average_scores": {"quality": 0.7}},
        }
        return summaries[agent_id]
    
    feedback_analyzer.feedback_manager.get_feedback_summary = MagicMock(
        side_effect=mock_get_feedback_summary
    )
    
    # Execute
    comparison = feedback_analyzer.compare_agents(agent_ids, metric)
    
    # Verify
    assert comparison["agent-1"] == 0.85
    assert comparison["agent-2"] == 0.9
    assert comparison["agent-3"] == 0.7


class TestFeedbackAwareAgent(FeedbackAwareAgent):
    """Test implementation of FeedbackAwareAgent."""
    
    def __init__(self, feedback_manager):
        """Initialize the test agent."""
        super().__init__(feedback_manager)
        self.id = "test-agent"
        self.learned_from = []
    
    async def learn_from_feedback(self, feedback_data):
        """Learn from feedback data."""
        self.learned_from.append(feedback_data)


@pytest.mark.asyncio
async def test_process_feedback(feedback_manager):
    """Test processing feedback."""
    # Setup
    agent = TestFeedbackAwareAgent(feedback_manager)
    
    # Mock the record_feedback method
    feedback_manager.record_feedback = MagicMock()
    
    # Create a feedback message
    feedback_message = MagicMock()
    feedback_message.sender = "sender-agent"
    feedback_message.payload = {
        "about_message_id": "message-123",
        "feedback_data": {
            "quality": 8,
            "relevance": 9,
            "suggestions": ["Improve clarity"],
        },
    }
    
    # Execute
    await agent.process_feedback(feedback_message)
    
    # Verify
    feedback_manager.record_feedback.assert_called_once_with(
        sender_id="sender-agent",
        recipient_id="test-agent",
        feedback_data=feedback_message.payload["feedback_data"],
        message_id="message-123",
    )
    
    assert len(agent.feedback_history) == 1
    assert agent.feedback_history[0]["sender"] == "sender-agent"
    assert agent.feedback_history[0]["about_message_id"] == "message-123"
    
    assert len(agent.learned_from) == 1
    assert agent.learned_from[0] == feedback_message.payload["feedback_data"]
