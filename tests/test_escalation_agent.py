"""
Tests for the Escalation Evaluator Agent.

Tests the agent that determines if tickets need human intervention.
"""

import pytest
from src.agents.escalation_agent import escalation_evaluator_agent


class TestEscalationAgent:
    """Test suite for Escalation Evaluator Agent."""

    def test_escalation_agent_keyword_auto_escalate(self, escalation_ticket_state, mock_chatgpt):
        """Test that escalation keywords trigger automatic escalation."""
        # Query contains "lawyer" - should auto-escalate
        # No LLM call should be made for keyword escalation

        # Run the agent
        result = escalation_evaluator_agent(escalation_ticket_state)

        # Assertions
        assert result["needs_escalation"] is True
        assert "[ESCALATION] Auto-escalated based on keywords" in result["conversation_history"][-1]

    def test_escalation_agent_lawsuit_keyword(self, resolved_ticket_state, mock_chatgpt):
        """Test 'lawsuit' keyword triggers escalation."""
        # Add lawsuit keyword
        resolved_ticket_state["customer_query"] = "This is unacceptable! I'm filing a lawsuit!"

        # Run the agent
        result = escalation_evaluator_agent(resolved_ticket_state)

        # Should auto-escalate
        assert result["needs_escalation"] is True

    def test_escalation_agent_urgent_keyword(self, resolved_ticket_state, mock_chatgpt):
        """Test 'urgent' keyword triggers escalation."""
        resolved_ticket_state["customer_query"] = "This is urgent! Need help now!"

        # Run the agent
        result = escalation_evaluator_agent(resolved_ticket_state)

        # Should auto-escalate
        assert result["needs_escalation"] is True

    def test_escalation_agent_angry_keyword(self, resolved_ticket_state, mock_chatgpt):
        """Test 'angry' keyword triggers escalation."""
        resolved_ticket_state["customer_query"] = "I'm so angry about this terrible service!"

        # Run the agent
        result = escalation_evaluator_agent(resolved_ticket_state)

        # Should auto-escalate
        assert result["needs_escalation"] is True

    def test_escalation_agent_llm_escalate_decision(self, resolved_ticket_state, mock_chatgpt):
        """Test LLM-based escalation decision when no keywords present."""
        # Query without escalation keywords
        resolved_ticket_state["customer_query"] = "I need access to sensitive financial records"
        resolved_ticket_state["resolution"] = "You can request access through the portal"

        # Mock LLM to return ESCALATE
        mock_chatgpt("ESCALATE")

        # Run the agent
        result = escalation_evaluator_agent(resolved_ticket_state)

        # Should escalate based on LLM decision
        assert result["needs_escalation"] is True
        assert "[ESCALATION] Marked for human review" in result["conversation_history"][-1]

    def test_escalation_agent_llm_resolve_decision(self, resolved_ticket_state, mock_chatgpt):
        """Test LLM decides not to escalate for simple issues."""
        # Simple query
        resolved_ticket_state["customer_query"] = "How do I change my password?"
        resolved_ticket_state["resolution"] = "Go to settings and click 'Change Password'"

        # Mock LLM to return RESOLVE
        mock_chatgpt("RESOLVE")

        # Run the agent
        result = escalation_evaluator_agent(resolved_ticket_state)

        # Should not escalate
        assert result["needs_escalation"] is False
        assert "[ESCALATION] Cleared for automated response" in result["conversation_history"][-1]

    def test_escalation_agent_complex_technical_issue(self, resolved_ticket_state, mock_chatgpt):
        """Test escalation for complex technical issues."""
        resolved_ticket_state["customer_query"] = "Critical system bug causing data corruption in production"
        resolved_ticket_state["category"] = "TECHNICAL"
        resolved_ticket_state["priority"] = "high"
        resolved_ticket_state["resolution"] = "This appears to be a critical bug"

        # Mock LLM to escalate
        mock_chatgpt("ESCALATE")

        # Run the agent
        result = escalation_evaluator_agent(resolved_ticket_state)

        # Should escalate
        assert result["needs_escalation"] is True

    def test_escalation_agent_high_value_refund(self, resolved_ticket_state, mock_chatgpt):
        """Test escalation for high-value refund requests."""
        resolved_ticket_state["customer_query"] = "I need a $5000 refund for the annual contract"
        resolved_ticket_state["category"] = "BILLING"

        # Mock LLM to escalate
        mock_chatgpt("ESCALATE")

        # Run the agent
        result = escalation_evaluator_agent(resolved_ticket_state)

        # Should escalate
        assert result["needs_escalation"] is True

    def test_escalation_agent_simple_faq_resolve(self, resolved_ticket_state, mock_chatgpt):
        """Test that simple FAQ-matched queries don't escalate."""
        resolved_ticket_state["customer_query"] = "How do I reset my password?"
        resolved_ticket_state["faq_match"] = "Click 'Forgot Password' on the login page"
        resolved_ticket_state["resolution"] = "Follow the forgot password link"

        # Mock LLM to resolve
        mock_chatgpt("RESOLVE")

        # Run the agent
        result = escalation_evaluator_agent(resolved_ticket_state)

        # Should not escalate
        assert result["needs_escalation"] is False

    def test_escalation_agent_preserves_state(self, resolved_ticket_state, mock_chatgpt):
        """Test that escalation agent doesn't modify unrelated state."""
        # Set up state
        resolved_ticket_state["ticket_id"] = "TKT-ESC999"
        resolved_ticket_state["category"] = "TECHNICAL"
        resolved_ticket_state["priority"] = "high"
        resolved_ticket_state["customer_query"] = "Simple question"

        # Mock LLM to resolve
        mock_chatgpt("RESOLVE")

        # Run the agent
        result = escalation_evaluator_agent(resolved_ticket_state)

        # These should remain unchanged
        assert result["ticket_id"] == "TKT-ESC999"
        assert result["category"] == "TECHNICAL"
        assert result["priority"] == "high"
        assert result["resolution"] == resolved_ticket_state["resolution"]

    def test_escalation_agent_case_insensitive_keywords(self, resolved_ticket_state, mock_chatgpt):
        """Test that keyword matching is case-insensitive."""
        # Mixed case keywords
        resolved_ticket_state["customer_query"] = "This is URGENT and CRITICAL!"

        # Run the agent
        result = escalation_evaluator_agent(resolved_ticket_state)

        # Should auto-escalate regardless of case
        assert result["needs_escalation"] is True

    def test_escalation_agent_multiple_keywords(self, resolved_ticket_state, mock_chatgpt):
        """Test handling of multiple escalation keywords."""
        resolved_ticket_state["customer_query"] = "I'm frustrated and angry! This is unacceptable!"

        # Run the agent
        result = escalation_evaluator_agent(resolved_ticket_state)

        # Should auto-escalate
        assert result["needs_escalation"] is True

    def test_escalation_agent_resolution_truncation(self, resolved_ticket_state, mock_chatgpt):
        """Test that long resolutions are truncated for LLM input."""
        # Very long resolution
        resolved_ticket_state["customer_query"] = "Simple question"
        resolved_ticket_state["resolution"] = "A" * 1000  # 1000 characters

        # Mock LLM response
        mock_chatgpt("RESOLVE")

        # Run the agent (should truncate resolution to 500 chars)
        result = escalation_evaluator_agent(resolved_ticket_state)

        # Should complete without error
        assert result is not None
        assert result["needs_escalation"] is False

    def test_escalation_agent_default_to_resolve(self, resolved_ticket_state, mock_chatgpt):
        """Test that unexpected LLM responses default to not escalating."""
        resolved_ticket_state["customer_query"] = "Simple question"

        # Mock LLM with unexpected response
        mock_chatgpt("MAYBE")  # Not ESCALATE or RESOLVE

        # Run the agent
        result = escalation_evaluator_agent(resolved_ticket_state)

        # Should default to not escalating (safer default)
        assert result["needs_escalation"] is False

    def test_escalation_agent_frustrated_customer(self, resolved_ticket_state, mock_chatgpt):
        """Test escalation for frustrated customers."""
        resolved_ticket_state["customer_query"] = "I've contacted support 5 times and no one has helped me!"

        # Mock LLM to escalate
        mock_chatgpt("ESCALATE")

        # Run the agent
        result = escalation_evaluator_agent(resolved_ticket_state)

        # Should escalate for frustrated customer
        assert result["needs_escalation"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
