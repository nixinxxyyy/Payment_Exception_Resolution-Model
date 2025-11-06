"""
Pytest fixtures and configuration for agent tests.
"""

import pytest
import os
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

# Set fake API key for tests to avoid authentication errors
os.environ['OPENAI_API_KEY'] = 'sk-test-fake-key-for-testing-only'


@pytest.fixture
def base_ticket_state() -> Dict[str, Any]:
    """Basic ticket state fixture for testing."""
    return {
        "customer_query": "I need help with my account",
        "ticket_id": "TKT-TEST001",
        "category": "",
        "faq_match": "",
        "resolution": "",
        "needs_escalation": False,
        "final_response": "",
        "conversation_history": [],
        "customer_email": "test@example.com",
        "priority": "medium",
        "timestamp": datetime.now().isoformat(),
        "metadata": {}
    }


@pytest.fixture
def technical_ticket_state() -> Dict[str, Any]:
    """Ticket state for technical issues."""
    return {
        "customer_query": "My application crashes when I upload large files over 100MB",
        "ticket_id": "TKT-TECH001",
        "category": "",
        "faq_match": "",
        "resolution": "",
        "needs_escalation": False,
        "final_response": "",
        "conversation_history": [],
        "customer_email": "tech@example.com",
        "priority": "medium",
        "timestamp": datetime.now().isoformat(),
        "metadata": {}
    }


@pytest.fixture
def billing_ticket_state() -> Dict[str, Any]:
    """Ticket state for billing issues."""
    return {
        "customer_query": "I was charged twice for my subscription this month",
        "ticket_id": "TKT-BILL001",
        "category": "",
        "faq_match": "",
        "resolution": "",
        "needs_escalation": False,
        "final_response": "",
        "conversation_history": [],
        "customer_email": "billing@example.com",
        "priority": "medium",
        "timestamp": datetime.now().isoformat(),
        "metadata": {}
    }


@pytest.fixture
def general_ticket_state() -> Dict[str, Any]:
    """Ticket state for general inquiries."""
    return {
        "customer_query": "How do I reset my password?",
        "ticket_id": "TKT-GEN001",
        "category": "",
        "faq_match": "",
        "resolution": "",
        "needs_escalation": False,
        "final_response": "",
        "conversation_history": [],
        "customer_email": "general@example.com",
        "priority": "medium",
        "timestamp": datetime.now().isoformat(),
        "metadata": {}
    }


@pytest.fixture
def urgent_ticket_state() -> Dict[str, Any]:
    """Ticket state with urgent keywords."""
    return {
        "customer_query": "URGENT: Critical system failure affecting all users!",
        "ticket_id": "TKT-URG001",
        "category": "",
        "faq_match": "",
        "resolution": "",
        "needs_escalation": False,
        "final_response": "",
        "conversation_history": [],
        "customer_email": "urgent@example.com",
        "priority": "medium",
        "timestamp": datetime.now().isoformat(),
        "metadata": {}
    }


@pytest.fixture
def escalation_ticket_state() -> Dict[str, Any]:
    """Ticket state that should trigger escalation."""
    return {
        "customer_query": "I want to speak to a lawyer about this unacceptable service!",
        "ticket_id": "TKT-ESC001",
        "category": "GENERAL",
        "faq_match": "",
        "resolution": "We apologize for the inconvenience...",
        "needs_escalation": False,
        "final_response": "",
        "conversation_history": [],
        "customer_email": "escalate@example.com",
        "priority": "high",
        "timestamp": datetime.now().isoformat(),
        "metadata": {}
    }


@pytest.fixture
def classified_ticket_state() -> Dict[str, Any]:
    """Ticket state that has been classified."""
    return {
        "customer_query": "My app is crashing",
        "ticket_id": "TKT-CLASS001",
        "category": "TECHNICAL",
        "faq_match": "",
        "resolution": "",
        "needs_escalation": False,
        "final_response": "",
        "conversation_history": ["[INTAKE] Customer reports app crash"],
        "customer_email": "classified@example.com",
        "priority": "high",
        "timestamp": datetime.now().isoformat(),
        "metadata": {}
    }


@pytest.fixture
def resolved_ticket_state() -> Dict[str, Any]:
    """Ticket state with resolution."""
    return {
        "customer_query": "How do I reset my password?",
        "ticket_id": "TKT-RES001",
        "category": "GENERAL",
        "faq_match": "Click 'Forgot Password' on the login page",
        "resolution": "To reset your password:\n1. Go to login page\n2. Click 'Forgot Password'\n3. Enter your email\n4. Check your email for reset link",
        "needs_escalation": False,
        "final_response": "",
        "conversation_history": [
            "[INTAKE] Customer asking about password reset",
            "[FAQ] Match found",
            "[CLASSIFIER] Category: GENERAL",
            "[GENERAL] Resolution provided"
        ],
        "customer_email": "resolved@example.com",
        "priority": "low",
        "timestamp": datetime.now().isoformat(),
        "metadata": {}
    }


@pytest.fixture
def sample_faq_database() -> Dict[str, Any]:
    """Sample FAQ database for testing."""
    return {
        "faqs": [
            {
                "id": 1,
                "category": "GENERAL",
                "question": "How do I reset my password?",
                "answer": "Click 'Forgot Password' on the login page and follow the instructions."
            },
            {
                "id": 2,
                "category": "TECHNICAL",
                "question": "Why is my app crashing?",
                "answer": "Try clearing your cache and updating to the latest version."
            },
            {
                "id": 3,
                "category": "BILLING",
                "question": "How do I cancel my subscription?",
                "answer": "Go to Account Settings > Billing > Cancel Subscription."
            },
            {
                "id": 4,
                "category": "BILLING",
                "question": "When will I be charged?",
                "answer": "You will be charged on the same day each month as your signup date."
            },
            {
                "id": 5,
                "category": "TECHNICAL",
                "question": "How do I upload files?",
                "answer": "Click the upload button and select files from your device."
            }
        ]
    }


@pytest.fixture
def mock_llm_response():
    """Mock LLM response."""
    def _create_mock(content: str):
        mock_response = Mock()
        mock_response.content = content
        return mock_response
    return _create_mock


@pytest.fixture
def mock_chatgpt():
    """
    Mock ChatOpenAI to avoid actual API calls.

    Usage:
        mock_chatgpt("Expected response content")
        result = agent(state)
    """
    # Store patches and shared mocks
    patches = []

    # Store the current response content (mutable container to allow updates)
    response_container = {'content': ''}

    # Create response object class
    class MockResponse:
        @property
        def content(self):
            return response_container['content']

    # Create a callable mock LLM that returns the response
    # LangChain's pipe operator wraps the LLM in a RunnableLambda which calls it
    def mock_llm_callable(*args, **kwargs):
        return MockResponse()

    mock_llm = Mock(side_effect=mock_llm_callable)
    mock_chat_class = Mock(return_value=mock_llm)

    # Patch ChatOpenAI in all agent modules (where it's used, not defined)
    agent_modules = [
        'src.agents.intake_agent',
        'src.agents.faq_agent',
        'src.agents.classifier_agent',
        'src.agents.technical_agent',
        'src.agents.billing_agent',
        'src.agents.general_agent',
        'src.agents.escalation_agent',
        'src.agents.response_agent',
    ]

    for module in agent_modules:
        patcher = patch(f'{module}.ChatOpenAI', mock_chat_class)
        patches.append(patcher)
        patcher.start()

    def _mock_with_response(response_content: str):
        # Update the response content
        response_container['content'] = response_content

    yield _mock_with_response

    # Cleanup: stop all patches
    for patcher in patches:
        patcher.stop()
