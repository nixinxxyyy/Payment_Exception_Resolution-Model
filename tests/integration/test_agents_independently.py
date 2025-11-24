"""
Integration tests for running each agent independently.

These tests can be run with real OpenAI API calls (if API key is set)
or skipped if no API key is available.

Run individual agent tests:
    pytest tests/integration/test_agents_independently.py::TestIntakeAgentIndependent -v
    pytest tests/integration/test_agents_independently.py::TestClassifierAgentIndependent -v
"""

import pytest
import os
from datetime import datetime

# Check if OpenAI API key is available
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
HAS_API_KEY = OPENAI_API_KEY and not OPENAI_API_KEY.startswith("sk-test")

# Skip all tests in this file if no real API key
pytestmark = pytest.mark.skipif(
    not HAS_API_KEY,
    reason="Requires real OPENAI_API_KEY for integration tests"
)


class TestIntakeAgentIndependent:
    """Test Intake Agent independently with real API calls."""

    def test_intake_agent_standalone(self):
        """Test intake agent can run standalone."""
        from src.agents.intake_agent import intake_agent

        state = {
            "customer_query": "My application is crashing when I try to upload files",
            "ticket_id": "TEST-INTAKE-001",
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

        result = intake_agent(state)

        # Verify agent execution
        assert result is not None
        assert result["ticket_id"] == "TEST-INTAKE-001"
        assert result["priority"] in ["low", "medium", "high"]
        assert len(result["conversation_history"]) > 0
        assert "[INTAKE]" in result["conversation_history"][0]

        print(f"\n✅ Intake Agent Test Passed")
        print(f"   Priority: {result['priority']}")
        print(f"   History: {result['conversation_history'][0][:100]}...")


class TestFAQAgentIndependent:
    """Test FAQ Lookup Agent independently."""

    def test_faq_agent_standalone(self):
        """Test FAQ agent can run standalone."""
        from src.agents.faq_agent import faq_lookup_agent

        state = {
            "customer_query": "How do I reset my password?",
            "ticket_id": "TEST-FAQ-001",
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

        result = faq_lookup_agent(state)

        # Verify agent execution
        assert result is not None
        assert "faq_match" in result
        assert len(result["conversation_history"]) > 0
        assert "[FAQ]" in result["conversation_history"][0]

        print(f"\n✅ FAQ Agent Test Passed")
        print(f"   FAQ Match: {result['faq_match'][:100] if result['faq_match'] else 'No match'}...")
        print(f"   History: {result['conversation_history'][0]}")


class TestClassifierAgentIndependent:
    """Test Classifier Agent independently."""

    def test_classifier_technical(self):
        """Test classifier with technical query."""
        from src.agents.classifier_agent import classifier_agent

        state = {
            "customer_query": "My app crashes when uploading files",
            "ticket_id": "TEST-CLASS-001",
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

        result = classifier_agent(state)

        # Verify agent execution
        assert result is not None
        assert result["category"] in ["TECHNICAL", "BILLING", "GENERAL", "UNKNOWN"]
        assert len(result["conversation_history"]) > 0

        print(f"\n✅ Classifier Agent Test Passed (Technical)")
        print(f"   Category: {result['category']}")
        print(f"   History: {result['conversation_history'][-1]}")

    def test_classifier_billing(self):
        """Test classifier with billing query."""
        from src.agents.classifier_agent import classifier_agent

        state = {
            "customer_query": "I was charged twice this month",
            "ticket_id": "TEST-CLASS-002",
            "category": "",
            "faq_match": "",
            "conversation_history": [],
            "customer_email": "test@example.com",
            "priority": "medium",
            "timestamp": datetime.now().isoformat(),
            "metadata": {}
        }

        result = classifier_agent(state)

        assert result["category"] in ["TECHNICAL", "BILLING", "GENERAL", "UNKNOWN"]
        print(f"\n✅ Classifier Agent Test Passed (Billing)")
        print(f"   Category: {result['category']}")


class TestTechnicalAgentIndependent:
    """Test Technical Support Agent independently."""

    def test_technical_agent_standalone(self):
        """Test technical agent can run standalone."""
        from src.agents.technical_agent import technical_support_agent

        state = {
            "customer_query": "My application crashes when I upload large files",
            "ticket_id": "TEST-TECH-001",
            "category": "TECHNICAL",
            "faq_match": "",
            "resolution": "",
            "needs_escalation": False,
            "final_response": "",
            "conversation_history": ["[CLASSIFIER] Category: TECHNICAL"],
            "customer_email": "test@example.com",
            "priority": "high",
            "timestamp": datetime.now().isoformat(),
            "metadata": {}
        }

        result = technical_support_agent(state)

        # Verify agent execution
        assert result is not None
        assert result["resolution"] != ""
        assert len(result["conversation_history"]) > 1

        print(f"\n✅ Technical Agent Test Passed")
        print(f"   Resolution length: {len(result['resolution'])} chars")
        print(f"   Preview: {result['resolution'][:150]}...")


class TestBillingAgentIndependent:
    """Test Billing Support Agent independently."""

    def test_billing_agent_standalone(self):
        """Test billing agent can run standalone."""
        from src.agents.billing_agent import billing_support_agent

        state = {
            "customer_query": "I was charged twice for my subscription",
            "ticket_id": "TEST-BILL-001",
            "category": "BILLING",
            "faq_match": "",
            "resolution": "",
            "needs_escalation": False,
            "final_response": "",
            "conversation_history": ["[CLASSIFIER] Category: BILLING"],
            "customer_email": "test@example.com",
            "priority": "high",
            "timestamp": datetime.now().isoformat(),
            "metadata": {}
        }

        result = billing_support_agent(state)

        # Verify agent execution
        assert result is not None
        assert result["resolution"] != ""
        assert len(result["conversation_history"]) > 1

        print(f"\n✅ Billing Agent Test Passed")
        print(f"   Resolution length: {len(result['resolution'])} chars")
        print(f"   Preview: {result['resolution'][:150]}...")


class TestGeneralAgentIndependent:
    """Test General Support Agent independently."""

    def test_general_agent_standalone(self):
        """Test general agent can run standalone."""
        from src.agents.general_agent import general_support_agent

        state = {
            "customer_query": "How do I change my email address?",
            "ticket_id": "TEST-GEN-001",
            "category": "GENERAL",
            "faq_match": "",
            "resolution": "",
            "needs_escalation": False,
            "final_response": "",
            "conversation_history": ["[CLASSIFIER] Category: GENERAL"],
            "customer_email": "test@example.com",
            "priority": "low",
            "timestamp": datetime.now().isoformat(),
            "metadata": {}
        }

        result = general_support_agent(state)

        # Verify agent execution
        assert result is not None
        assert result["resolution"] != ""
        assert len(result["conversation_history"]) > 1

        print(f"\n✅ General Agent Test Passed")
        print(f"   Resolution length: {len(result['resolution'])} chars")
        print(f"   Preview: {result['resolution'][:150]}...")


class TestEscalationAgentIndependent:
    """Test Escalation Evaluator Agent independently."""

    def test_escalation_agent_no_escalation(self):
        """Test escalation agent with simple query."""
        from src.agents.escalation_agent import escalation_evaluator_agent

        state = {
            "customer_query": "How do I reset my password?",
            "ticket_id": "TEST-ESC-001",
            "category": "GENERAL",
            "faq_match": "Click 'Forgot Password'",
            "resolution": "Follow the forgot password link on the login page",
            "needs_escalation": False,
            "final_response": "",
            "conversation_history": [],
            "customer_email": "test@example.com",
            "priority": "low",
            "timestamp": datetime.now().isoformat(),
            "metadata": {}
        }

        result = escalation_evaluator_agent(state)

        # Verify agent execution
        assert result is not None
        assert "needs_escalation" in result
        assert len(result["conversation_history"]) > 0

        print(f"\n✅ Escalation Agent Test Passed (No Escalation)")
        print(f"   Needs Escalation: {result['needs_escalation']}")

    def test_escalation_agent_with_keyword(self):
        """Test escalation agent with escalation keyword."""
        from src.agents.escalation_agent import escalation_evaluator_agent

        state = {
            "customer_query": "This is urgent! I need help immediately!",
            "ticket_id": "TEST-ESC-002",
            "category": "TECHNICAL",
            "faq_match": "",
            "resolution": "We're looking into this",
            "needs_escalation": False,
            "final_response": "",
            "conversation_history": [],
            "customer_email": "test@example.com",
            "priority": "high",
            "timestamp": datetime.now().isoformat(),
            "metadata": {}
        }

        result = escalation_evaluator_agent(state)

        # Should auto-escalate due to "urgent" keyword
        assert result["needs_escalation"] is True

        print(f"\n✅ Escalation Agent Test Passed (Auto-Escalate)")
        print(f"   Needs Escalation: {result['needs_escalation']}")
        print(f"   Reason: Keyword detected")


class TestEscalationResponseAgentIndependent:
    """Test Escalation Response Agent independently."""

    def test_escalation_response_agent_standalone(self):
        """Test escalation response agent can run standalone."""
        from src.agents.escalation_response_agent import escalation_response_agent

        state = {
            "customer_query": "I need a full refund of $2000 for this broken service!",
            "ticket_id": "TEST-ESCRESP-001",
            "category": "BILLING",
            "faq_match": "",
            "resolution": "High-value refund requires account verification and approval",
            "needs_escalation": True,
            "final_response": "",
            "conversation_history": [
                "[INTAKE] Customer requesting refund",
                "[FAQ] No match found",
                "[CLASSIFIER] Category: BILLING",
                "[BILLING] Resolution provided",
                "[ESCALATION] Marked for human review"
            ],
            "customer_email": "test@example.com",
            "priority": "high",
            "timestamp": datetime.now().isoformat(),
            "metadata": {}
        }

        result = escalation_response_agent(state)

        # Verify agent execution
        assert result is not None
        assert result["final_response"] != ""
        assert len(result["conversation_history"]) > 5
        assert "[ESCALATION RESPONSE]" in result["conversation_history"][-1]

        print(f"\n✅ Escalation Response Agent Test Passed")
        print(f"   Response length: {len(result['final_response'])} chars")
        print(f"   Preview: {result['final_response'][:150]}...")

    def test_escalation_response_technical_issue(self):
        """Test escalation response for technical category."""
        from src.agents.escalation_response_agent import escalation_response_agent

        state = {
            "customer_query": "Critical bug in production causing data loss!",
            "ticket_id": "TEST-ESCRESP-002",
            "category": "TECHNICAL",
            "faq_match": "",
            "resolution": "Critical system issue requiring engineering investigation",
            "needs_escalation": True,
            "final_response": "",
            "conversation_history": [
                "[INTAKE] Customer reports critical bug",
                "[CLASSIFIER] Category: TECHNICAL",
                "[TECHNICAL] Resolution provided",
                "[ESCALATION] Marked for human review"
            ],
            "customer_email": "test@example.com",
            "priority": "high",
            "timestamp": datetime.now().isoformat(),
            "metadata": {}
        }

        result = escalation_response_agent(state)

        # Verify escalation response generated
        assert result is not None
        assert result["final_response"] != ""

        print(f"\n✅ Escalation Response Agent Test Passed (Technical)")
        print(f"   Category: {result['category']}")
        print(f"   Response: {result['final_response'][:100]}...")


class TestResponseAgentIndependent:
    """Test Response Generator Agent independently."""

    def test_response_agent_standalone(self):
        """Test response agent can run standalone."""
        from src.agents.response_agent import response_generator_agent

        state = {
            "customer_query": "How do I reset my password?",
            "ticket_id": "TEST-RESP-001",
            "category": "GENERAL",
            "faq_match": "Click 'Forgot Password'",
            "resolution": "To reset your password:\n1. Go to login page\n2. Click 'Forgot Password'\n3. Follow email instructions",
            "needs_escalation": False,
            "final_response": "",
            "conversation_history": [
                "[INTAKE] Customer asking about password",
                "[FAQ] Match found",
                "[CLASSIFIER] Category: GENERAL",
                "[GENERAL] Resolution provided"
            ],
            "customer_email": "test@example.com",
            "priority": "low",
            "timestamp": datetime.now().isoformat(),
            "metadata": {}
        }

        result = response_generator_agent(state)

        # Verify agent execution
        assert result is not None
        assert result["final_response"] != ""
        assert len(result["conversation_history"]) > 4

        print(f"\n✅ Response Agent Test Passed")
        print(f"   Response length: {len(result['final_response'])} chars")
        print(f"   Preview: {result['final_response'][:150]}...")


if __name__ == "__main__":
    # Allow running individual test classes
    import sys

    if len(sys.argv) > 1:
        test_class = sys.argv[1]
        pytest.main([__file__, f"-k {test_class}", "-v", "-s"])
    else:
        pytest.main([__file__, "-v", "-s"])
