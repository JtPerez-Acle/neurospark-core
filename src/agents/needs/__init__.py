"""Needs expression module for NeuroSpark Core.

This module provides needs expression and fulfillment capabilities for agents.
"""

from src.agents.needs.protocol import NeedsProtocol, NeedsFulfillmentMixin, NeedsExpressionMixin

__all__ = [
    "NeedsProtocol",
    "NeedsFulfillmentMixin",
    "NeedsExpressionMixin",
]
