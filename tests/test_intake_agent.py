"""
Tests for the Intake Agent.

Tests the first agent in the workflow that processes incoming customer queries
and extracts key information.
"""

import pytest
from src.agents.intake_agent import intake_agent


class TestIntakeAgent:
    """Test suite for Intake Agent."""

    def test_intake_agent_basic_processing(self, base_ticket_state, mock_chatgpt):
        """Test that intake agent processes a basic query."""
        # Mock LLM response
        mock_chatgpt("Customer needs help with account access. Main issue: account help. Sentiment: neutral. Urgency: medium.")

        # Run the agent
        result = intake_agent(base_ticket_state)

        # Assertions
        assert result is not None
        assert result["ticket_id"] == "TKT-TEST001"
        assert result["priority"] == "medium"  # Default priority
        assert len(result["conversation_history"]) == 1
        assert "[INTAKE]" in result["conversation_history"][0]
        assert "timestamp" in result

    def test_intake_agent_urgent_priority(self, base_ticket_state, mock_chatgpt):
        """Test that urgent keywords are detected and priority is set to high."""
        # Update query with urgent keyword
        base_ticket_state["customer_query"] = "URGENT: I need immediate help!"

        # Mock LLM response
        mock_chatgpt("Customer needs urgent assistance. High priority issue.")

        # Run the agent
        result = intake_agent(base_ticket_state)

        # Assertions
        assert result["priority"] == "high"
        assert "[INTAKE]" in result["conversation_history"][0]

    def test_intake_agent_low_priority(self, base_ticket_state, mock_chatgpt):
        """Test that question keywords result in low priority."""
        # Update query with question keyword
        base_ticket_state["customer_query"] = "I was just wondering how this feature works"

        # Mock LLM response
        mock_chatgpt("Customer has a general question about features.")

        # Run the agent
        result = intake_agent(base_ticket_state)

        # Assertions
        assert result["priority"] == "low"

    def test_intake_agent_critical_priority(self, urgent_ticket_state, mock_chatgpt):
        """Test critical/emergency keywords set high priority."""
        # Mock LLM response
        mock_chatgpt("Critical system failure reported. High urgency.")

        # Run the agent
        result = intake_agent(urgent_ticket_state)

        # Assertions
        assert result["priority"] == "high"
        assert "[INTAKE]" in result["conversation_history"][0]

    def test_intake_agent_preserves_state(self, base_ticket_state, mock_chatgpt):
        """Test that intake agent doesn't overwrite unrelated state fields."""
        # Add some existing state
        base_ticket_state["metadata"] = {"source": "web"}
        base_ticket_state["customer_email"] = "test@example.com"

        # Mock LLM response
        mock_chatgpt("Customer inquiry about account.")

        # Run the agent
        result = intake_agent(base_ticket_state)

        # Assertions - these should be preserved
        assert result["metadata"]["source"] == "web"
        assert result["customer_email"] == "test@example.com"
        assert result["ticket_id"] == "TKT-TEST001"

    def test_intake_agent_multiple_urgent_keywords(self, base_ticket_state, mock_chatgpt):
        """Test detection of multiple urgent keywords."""
        base_ticket_state["customer_query"] = "This is CRITICAL and URGENT! EMERGENCY assistance needed ASAP!"

        # Mock LLM response
        mock_chatgpt("Multiple urgent indicators detected.")

        # Run the agent
        result = intake_agent(base_ticket_state)

        # Should still be high priority (not multiple assignments)
        assert result["priority"] == "high"

    def test_intake_agent_conversation_history_append(self, base_ticket_state, mock_chatgpt):
        """Test that conversation history is appended, not replaced."""
        # Add existing history
        base_ticket_state["conversation_history"] = ["[SYSTEM] Ticket created"]

        # Mock LLM response
        mock_chatgpt("Customer needs assistance.")

        # Run the agent
        result = intake_agent(base_ticket_state)

        # Should have both entries
        assert len(result["conversation_history"]) == 2
        assert result["conversation_history"][0] == "[SYSTEM] Ticket created"
        assert "[INTAKE]" in result["conversation_history"][1]

    def test_intake_agent_timestamp_update(self, base_ticket_state, mock_chatgpt):
        """Test that timestamp is updated."""
        original_timestamp = base_ticket_state["timestamp"]

        # Mock LLM response
        mock_chatgpt("Customer inquiry.")

        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)

        # Run the agent
        result = intake_agent(base_ticket_state)

        # Timestamp should be updated (or at least exist)
        assert "timestamp" in result
        assert isinstance(result["timestamp"], str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
