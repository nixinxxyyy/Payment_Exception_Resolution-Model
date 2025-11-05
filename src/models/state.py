"""
State definitions for the multi-agent ticket management system.
"""

from enum import Enum
from typing import TypedDict, List, Optional


class TicketCategory(str, Enum):
    """Categories for customer support tickets."""
    TECHNICAL = "TECHNICAL"
    BILLING = "BILLING"
    GENERAL = "GENERAL"
    UNKNOWN = "UNKNOWN"


class TicketState(TypedDict):
    """
    State structure that flows through the multi-agent system.

    Attributes:
        customer_query: Original customer support query
        ticket_id: Unique identifier for the ticket
        category: Classification of the ticket (TECHNICAL/BILLING/GENERAL)
        faq_match: Any matching FAQ entry found
        resolution: Proposed resolution from specialized agent
        needs_escalation: Flag indicating if human intervention is needed
        final_response: Final response to send to customer
        conversation_history: Log of all agent interactions
        customer_email: Optional customer email
        priority: Priority level (low, medium, high)
        timestamp: Timestamp of ticket creation
        metadata: Additional metadata for the ticket
    """
    customer_query: str
    ticket_id: str
    category: str
    faq_match: str
    resolution: str
    needs_escalation: bool
    final_response: str
    conversation_history: List[str]
    customer_email: Optional[str]
    priority: str
    timestamp: str
    metadata: dict
