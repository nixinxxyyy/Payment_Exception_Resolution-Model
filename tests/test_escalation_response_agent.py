"""
Tests for the Escalation Response Agent.

Tests the agent that generates customer-facing responses for escalated tickets.
"""

import pytest
from src.agents.escalation_response_agent import escalation_response_agent


class TestEscalationResponseAgent:
    """Test suite for Escalation Response Agent."""

    def test_escalation_response_basic(self, escalation_ticket_state, mock_chatgpt):
        """Test basic escalation response generation."""
        # Mock LLM response
        mock_chatgpt(
            "Thank you for reaching out. I understand your concerns are important. "
            "Your ticket (TKT-ESC001) has been escalated to our specialist team who "
            "will review your case and respond within 24 hours."
        )

        # Run the agent
        result = escalation_response_agent(escalation_ticket_state)

        # Assertions
        assert result["final_response"] != ""
        assert "TKT-ESC001" in result["final_response"] or "ticket" in result["final_response"].lower()
        assert "[ESCALATION RESPONSE] Customer notification generated" in result["conversation_history"][-1]

    def test_escalation_response_includes_ticket_context(self, escalation_ticket_state, mock_chatgpt):
        """Test that escalation response includes relevant ticket context."""
        mock_chatgpt(
            "We appreciate you contacting us about your service concerns. "
            "Your issue requires specialized attention from our team. "
            "Ticket TKT-ESC001 has been prioritized for review by a senior specialist."
        )

        # Run the agent
        result = escalation_response_agent(escalation_ticket_state)

        # Should have generated a response
        assert result["final_response"] != ""
        assert len(result["final_response"]) > 50  # Reasonable length

    def test_escalation_response_technical_category(self, classified_ticket_state, mock_chatgpt):
        """Test escalation response for technical category tickets."""
        # Set as escalated
        classified_ticket_state["needs_escalation"] = True
        classified_ticket_state["resolution"] = "Requires investigation by engineering team"

        mock_chatgpt(
            "Thank you for reporting this technical issue. Your ticket (TKT-CLASS001) "
            "has been escalated to our engineering team for thorough investigation. "
            "A specialist will review the application crash and respond within 24 hours "
            "with a detailed analysis and resolution plan."
        )

        # Run the agent
        result = escalation_response_agent(classified_ticket_state)

        # Verify response generated
        assert result["final_response"] != ""
        assert "technical" in result["final_response"].lower() or "engineering" in result["final_response"].lower()

    def test_escalation_response_billing_category(self, billing_ticket_state, mock_chatgpt):
        """Test escalation response for billing category tickets."""
        # Set as escalated
        billing_ticket_state["needs_escalation"] = True
        billing_ticket_state["category"] = "BILLING"
        billing_ticket_state["resolution"] = "Requires account verification and refund processing"

        mock_chatgpt(
            "Thank you for contacting us about your billing concern. I understand how important "
            "account accuracy is to you. Your ticket (TKT-BILL001) has been escalated to our "
            "billing specialists who will carefully review your account and respond within 24 hours."
        )

        # Run the agent
        result = escalation_response_agent(billing_ticket_state)

        # Verify response
        assert result["final_response"] != ""
        assert "billing" in result["final_response"].lower() or "account" in result["final_response"].lower()

    def test_escalation_response_high_priority(self, urgent_ticket_state, mock_chatgpt):
        """Test escalation response for high priority tickets."""
        urgent_ticket_state["needs_escalation"] = True
        urgent_ticket_state["priority"] = "high"
        urgent_ticket_state["category"] = "TECHNICAL"
        urgent_ticket_state["resolution"] = "Critical system issue requiring immediate attention"

        mock_chatgpt(
            "We understand the urgency of your situation. Your critical system failure report "
            "(TKT-URG001) has been escalated to our senior technical team with high priority. "
            "A specialist will review this immediately and respond within 4 hours with an "
            "action plan to resolve this issue."
        )

        # Run the agent
        result = escalation_response_agent(urgent_ticket_state)

        # Verify response
        assert result["final_response"] != ""
        # Should mention urgency or priority
        assert any(word in result["final_response"].lower() for word in ["urgent", "priority", "immediate", "critical"])

    def test_escalation_response_preserves_state(self, escalation_ticket_state, mock_chatgpt):
        """Test that escalation response agent doesn't modify unrelated state fields."""
        # Set up known state
        escalation_ticket_state["ticket_id"] = "TKT-PRESERVE001"
        escalation_ticket_state["category"] = "BILLING"
        escalation_ticket_state["priority"] = "high"
        escalation_ticket_state["needs_escalation"] = True
        original_resolution = escalation_ticket_state["resolution"]

        mock_chatgpt("Your ticket has been escalated. We'll respond within 24 hours.")

        # Run the agent
        result = escalation_response_agent(escalation_ticket_state)

        # These should remain unchanged
        assert result["ticket_id"] == "TKT-PRESERVE001"
        assert result["category"] == "BILLING"
        assert result["priority"] == "high"
        assert result["needs_escalation"] is True
        assert result["resolution"] == original_resolution

    def test_escalation_response_adds_conversation_history(self, escalation_ticket_state, mock_chatgpt):
        """Test that escalation response agent adds to conversation history."""
        initial_history_length = len(escalation_ticket_state["conversation_history"])

        mock_chatgpt("Escalation message generated.")

        # Run the agent
        result = escalation_response_agent(escalation_ticket_state)

        # Should add exactly one entry
        assert len(result["conversation_history"]) == initial_history_length + 1
        assert "[ESCALATION RESPONSE] Customer notification generated" in result["conversation_history"][-1]

    def test_escalation_response_empathetic_tone(self, escalation_ticket_state, mock_chatgpt):
        """Test that escalation responses have empathetic tone."""
        escalation_ticket_state["customer_query"] = "I'm so frustrated! I've been waiting for days with no response!"

        mock_chatgpt(
            "I sincerely apologize for the delay and frustration you've experienced. "
            "Your concerns are completely valid, and I want to ensure you receive the attention "
            "you deserve. Your ticket (TKT-ESC001) has been escalated to a senior specialist "
            "who will personally handle your case and respond within 24 hours. "
            "We truly appreciate your patience and will make this right."
        )

        # Run the agent
        result = escalation_response_agent(escalation_ticket_state)

        # Response should be empathetic (look for empathy indicators)
        response_lower = result["final_response"].lower()
        empathy_indicators = ["understand", "appreciate", "apologize", "sorry", "important", "sincerely"]
        assert any(indicator in response_lower for indicator in empathy_indicators)

    def test_escalation_response_professional_format(self, escalation_ticket_state, mock_chatgpt):
        """Test that escalation response maintains professional format."""
        mock_chatgpt(
            "Dear Customer,\n\n"
            "Thank you for reaching out regarding your service concern. "
            "Your ticket (TKT-ESC001) has been escalated to our specialist team.\n\n"
            "A dedicated agent will review your case and respond within 24 hours.\n\n"
            "Best regards,\n"
            "Customer Support Team"
        )

        # Run the agent
        result = escalation_response_agent(escalation_ticket_state)

        # Should have a structured response
        assert result["final_response"] != ""
        assert len(result["final_response"]) > 30  # Reasonable minimum length

    def test_escalation_response_with_long_resolution(self, escalation_ticket_state, mock_chatgpt):
        """Test escalation response with lengthy internal resolution notes."""
        # Very long resolution
        escalation_ticket_state["resolution"] = (
            "This is a complex issue that requires detailed investigation. " * 50
        )

        mock_chatgpt(
            "Thank you for your detailed inquiry. Your ticket has been escalated "
            "to our specialist team for comprehensive review."
        )

        # Run the agent (should handle long resolution gracefully)
        result = escalation_response_agent(escalation_ticket_state)

        # Should complete without error
        assert result is not None
        assert result["final_response"] != ""

    def test_escalation_response_with_missing_optional_fields(self, base_ticket_state, mock_chatgpt):
        """Test escalation response when optional state fields are missing."""
        # Minimal state
        base_ticket_state["needs_escalation"] = True

        mock_chatgpt(
            "Your ticket has been escalated to our team for specialized attention. "
            "A specialist will respond within 24 hours."
        )

        # Run the agent
        result = escalation_response_agent(base_ticket_state)

        # Should still generate response
        assert result["final_response"] != ""

    def test_escalation_response_general_category(self, general_ticket_state, mock_chatgpt):
        """Test escalation response for general category tickets."""
        general_ticket_state["needs_escalation"] = True
        general_ticket_state["category"] = "GENERAL"
        general_ticket_state["resolution"] = "Requires account access verification"

        mock_chatgpt(
            "Thank you for contacting us. Your inquiry requires specialized review "
            "that goes beyond our standard support procedures. Your ticket (TKT-GEN001) "
            "has been escalated to a specialist who will personally handle your request "
            "and respond within 24 hours."
        )

        # Run the agent
        result = escalation_response_agent(general_ticket_state)

        # Verify response generated
        assert result["final_response"] != ""
        assert len(result["final_response"]) > 50

    def test_escalation_response_medium_priority(self, resolved_ticket_state, mock_chatgpt):
        """Test escalation response for medium priority tickets."""
        resolved_ticket_state["needs_escalation"] = True
        resolved_ticket_state["priority"] = "medium"

        mock_chatgpt(
            "Thank you for reaching out. Your ticket (TKT-RES001) has been escalated "
            "to our support team for detailed review. A specialist will respond within 24 hours."
        )

        # Run the agent
        result = escalation_response_agent(resolved_ticket_state)

        # Verify
        assert result["final_response"] != ""

    def test_escalation_response_sets_final_response_field(self, escalation_ticket_state, mock_chatgpt):
        """Test that escalation response agent specifically sets final_response field."""
        # Ensure final_response is initially empty
        assert escalation_ticket_state["final_response"] == ""

        mock_chatgpt("Your ticket has been escalated. We will respond soon.")

        # Run the agent
        result = escalation_response_agent(escalation_ticket_state)

        # final_response should now be populated
        assert result["final_response"] != ""
        assert result["final_response"] == "Your ticket has been escalated. We will respond soon."

    def test_escalation_response_ticket_id_reference(self, base_ticket_state, mock_chatgpt):
        """Test that escalation response includes ticket ID for reference."""
        base_ticket_state["ticket_id"] = "TKT-REF-12345"
        base_ticket_state["needs_escalation"] = True

        mock_chatgpt(
            "Your ticket (TKT-REF-12345) has been escalated for specialized review. "
            "Please reference this ticket ID in any follow-up communications."
        )

        # Run the agent
        result = escalation_response_agent(base_ticket_state)

        # Should reference the ticket ID
        assert "TKT-REF-12345" in result["final_response"] or "ticket" in result["final_response"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
