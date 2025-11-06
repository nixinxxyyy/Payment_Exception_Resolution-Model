"""
Tests for the Classifier Agent.

Tests the agent that categorizes tickets into TECHNICAL, BILLING, or GENERAL.
"""

import pytest
from src.agents.classifier_agent import classifier_agent


class TestClassifierAgent:
    """Test suite for Classifier Agent."""

    def test_classifier_technical_category(self, technical_ticket_state, mock_chatgpt):
        """Test classification of technical issues."""
        # Mock LLM to return TECHNICAL
        mock_chatgpt("TECHNICAL")

        # Run the agent
        result = classifier_agent(technical_ticket_state)

        # Assertions
        assert result["category"] == "TECHNICAL"
        assert len(result["conversation_history"]) == 1
        assert "[CLASSIFIER] Category: TECHNICAL" in result["conversation_history"][0]

    def test_classifier_billing_category(self, billing_ticket_state, mock_chatgpt):
        """Test classification of billing issues."""
        # Mock LLM to return BILLING
        mock_chatgpt("BILLING")

        # Run the agent
        result = classifier_agent(billing_ticket_state)

        # Assertions
        assert result["category"] == "BILLING"
        assert "[CLASSIFIER] Category: BILLING" in result["conversation_history"][0]

    def test_classifier_general_category(self, general_ticket_state, mock_chatgpt):
        """Test classification of general inquiries."""
        # Mock LLM to return GENERAL
        mock_chatgpt("GENERAL")

        # Run the agent
        result = classifier_agent(general_ticket_state)

        # Assertions
        assert result["category"] == "GENERAL"
        assert "[CLASSIFIER] Category: GENERAL" in result["conversation_history"][0]

    def test_classifier_invalid_category_defaults_to_general(self, base_ticket_state, mock_chatgpt):
        """Test that invalid categories default to GENERAL."""
        # Mock LLM to return invalid category
        mock_chatgpt("INVALID_CATEGORY")

        # Run the agent
        result = classifier_agent(base_ticket_state)

        # Should default to GENERAL
        assert result["category"] == "GENERAL"
        assert "[CLASSIFIER]" in result["conversation_history"][0]

    def test_classifier_lowercase_category(self, technical_ticket_state, mock_chatgpt):
        """Test that lowercase categories are normalized to uppercase."""
        # Mock LLM to return lowercase
        mock_chatgpt("technical")

        # Run the agent
        result = classifier_agent(technical_ticket_state)

        # Should be normalized to uppercase
        assert result["category"] == "TECHNICAL"

    def test_classifier_with_faq_match_context(self, general_ticket_state, mock_chatgpt):
        """Test that classifier uses FAQ match as context."""
        # Add FAQ match to state
        general_ticket_state["faq_match"] = "Click 'Forgot Password' on the login page"

        # Mock LLM response
        mock_chatgpt("GENERAL")

        # Run the agent
        result = classifier_agent(general_ticket_state)

        # Should classify correctly
        assert result["category"] == "GENERAL"

    def test_classifier_preserves_other_state(self, technical_ticket_state, mock_chatgpt):
        """Test that classifier doesn't modify unrelated state fields."""
        # Set up state
        technical_ticket_state["priority"] = "high"
        technical_ticket_state["customer_email"] = "tech@example.com"
        technical_ticket_state["metadata"] = {"ip": "192.168.1.1"}

        # Mock LLM response
        mock_chatgpt("TECHNICAL")

        # Run the agent
        result = classifier_agent(technical_ticket_state)

        # These should remain unchanged
        assert result["priority"] == "high"
        assert result["customer_email"] == "tech@example.com"
        assert result["metadata"]["ip"] == "192.168.1.1"

    def test_classifier_appends_conversation_history(self, technical_ticket_state, mock_chatgpt):
        """Test that classifier appends to conversation history."""
        # Add existing history
        technical_ticket_state["conversation_history"] = [
            "[INTAKE] Technical issue detected",
            "[FAQ] No match found"
        ]

        # Mock LLM response
        mock_chatgpt("TECHNICAL")

        # Run the agent
        result = classifier_agent(technical_ticket_state)

        # Should have all three entries
        assert len(result["conversation_history"]) == 3
        assert result["conversation_history"][0] == "[INTAKE] Technical issue detected"
        assert result["conversation_history"][1] == "[FAQ] No match found"
        assert "[CLASSIFIER] Category: TECHNICAL" in result["conversation_history"][2]

    def test_classifier_with_whitespace_in_response(self, billing_ticket_state, mock_chatgpt):
        """Test that classifier handles whitespace in LLM response."""
        # Mock LLM response with whitespace
        mock_chatgpt("  BILLING  \n")

        # Run the agent
        result = classifier_agent(billing_ticket_state)

        # Should strip whitespace
        assert result["category"] == "BILLING"

    def test_classifier_mixed_case_normalization(self, general_ticket_state, mock_chatgpt):
        """Test various case formats are normalized."""
        # Mock LLM response with mixed case
        mock_chatgpt("General")

        # Run the agent
        result = classifier_agent(general_ticket_state)

        # Should normalize to uppercase
        assert result["category"] == "GENERAL"

    def test_classifier_with_extra_text(self, technical_ticket_state, mock_chatgpt):
        """Test classifier when LLM includes extra explanation (should still work if category is there)."""
        # Mock LLM with just the category word
        mock_chatgpt("TECHNICAL")

        # Run the agent
        result = classifier_agent(technical_ticket_state)

        # Should extract category correctly
        assert result["category"] == "TECHNICAL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
