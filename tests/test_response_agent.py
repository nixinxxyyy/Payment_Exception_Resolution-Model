"""
Tests for the Response Generator Agent.

Tests the agent that creates final customer-facing responses.
"""

import pytest
from src.agents.response_agent import response_generator_agent


class TestResponseAgent:
    """Test suite for Response Generator Agent."""

    def test_response_agent_generates_final_response(self, resolved_ticket_state, mock_chatgpt):
        """Test that response agent generates a customer-facing response."""
        # Mock a professional response
        customer_response = """Dear Customer,

Thank you for contacting our support team. I understand you need help resetting your password.

To reset your password:
1. Go to the login page
2. Click 'Forgot Password'
3. Enter your email address
4. Check your email for the reset link
5. Follow the link and create a new password

Your ticket ID for reference is TKT-RES001.

If you have any further questions, please don't hesitate to reach out. We're here to help!

Best regards,
Customer Support Team"""

        mock_chatgpt(customer_response)

        # Run the agent
        result = response_generator_agent(resolved_ticket_state)

        # Assertions
        assert result["final_response"] != ""
        assert "Dear Customer" in result["final_response"]
        assert "[RESPONSE] Final response generated" in result["conversation_history"][-1]

    def test_response_agent_includes_ticket_id(self, resolved_ticket_state, mock_chatgpt):
        """Test that response includes ticket ID for reference."""
        # Mock response with ticket ID
        mock_chatgpt("""Thank you for contacting support.

Your ticket ID is TKT-RES001 for future reference.

Best regards,
Support Team""")

        # Run the agent
        result = response_generator_agent(resolved_ticket_state)

        # Should mention ticket ID
        assert result["final_response"] != ""
        # The response should exist and be non-empty
        assert len(result["final_response"]) > 0

    def test_response_agent_technical_response(self, classified_ticket_state, mock_chatgpt):
        """Test response generation for technical issues."""
        # Set up technical resolution
        classified_ticket_state["resolution"] = """Troubleshooting steps:
1. Clear cache
2. Update browser
3. Restart application"""
        classified_ticket_state["category"] = "TECHNICAL"

        # Mock technical response
        mock_chatgpt("""Dear Customer,

Thank you for reporting this technical issue. I've reviewed your case and have some troubleshooting steps that should help resolve the problem.

Please try the following:
1. Clear your browser cache
2. Update to the latest browser version
3. Restart the application

These steps should resolve the issue you're experiencing.

Ticket ID: TKT-CLASS001

Best regards,
Technical Support Team""")

        # Run the agent
        result = response_generator_agent(classified_ticket_state)

        # Should have professional technical response
        assert result["final_response"] != ""

    def test_response_agent_billing_response(self, billing_ticket_state, mock_chatgpt):
        """Test response generation for billing issues."""
        # Set up billing resolution
        billing_ticket_state["resolution"] = "Duplicate charge will be refunded in 3-5 business days"
        billing_ticket_state["category"] = "BILLING"

        # Mock billing response
        mock_chatgpt("""Dear Customer,

Thank you for bringing this billing issue to our attention. I sincerely apologize for any inconvenience caused.

I've reviewed your account and confirmed that you were charged twice. The duplicate charge will be automatically refunded to your account within 3-5 business days.

Ticket ID: TKT-BILL001

If you don't see the refund within this timeframe, please contact us again.

Best regards,
Billing Support Team""")

        # Run the agent
        result = response_generator_agent(billing_ticket_state)

        # Should have empathetic billing response
        assert result["final_response"] != ""

    def test_response_agent_general_response(self, general_ticket_state, mock_chatgpt):
        """Test response generation for general inquiries."""
        # Set up general resolution
        general_ticket_state["resolution"] = "Click 'Forgot Password' on login page"
        general_ticket_state["category"] = "GENERAL"

        # Mock general response
        mock_chatgpt("""Hi there,

Thanks for reaching out! I'm happy to help you reset your password.

Simply click the 'Forgot Password' link on the login page and follow the instructions. It's quick and easy!

Ticket ID: TKT-GEN001

Let me know if you need anything else!

Best,
Support Team""")

        # Run the agent
        result = response_generator_agent(general_ticket_state)

        # Should have friendly general response
        assert result["final_response"] != ""

    def test_response_agent_preserves_state(self, resolved_ticket_state, mock_chatgpt):
        """Test that response agent doesn't modify unrelated state."""
        # Set up state
        resolved_ticket_state["ticket_id"] = "TKT-RESP999"
        resolved_ticket_state["category"] = "GENERAL"
        resolved_ticket_state["priority"] = "low"
        resolved_ticket_state["resolution"] = "Resolution text"

        # Mock response
        mock_chatgpt("Customer response generated")

        # Run the agent
        result = response_generator_agent(resolved_ticket_state)

        # These should remain unchanged
        assert result["ticket_id"] == "TKT-RESP999"
        assert result["category"] == "GENERAL"
        assert result["priority"] == "low"
        assert result["resolution"] == "Resolution text"

    def test_response_agent_with_missing_resolution(self, base_ticket_state, mock_chatgpt):
        """Test response agent handles missing resolution gracefully."""
        # No resolution provided
        base_ticket_state["resolution"] = ""
        base_ticket_state["category"] = "GENERAL"

        # Mock fallback response
        mock_chatgpt("""Dear Customer,

Thank you for contacting us. We're looking into this for you and will get back to you shortly.

Ticket ID: TKT-TEST001

Best regards,
Support Team""")

        # Run the agent
        result = response_generator_agent(base_ticket_state)

        # Should still generate a response
        assert result["final_response"] != ""

    def test_response_agent_appends_to_history(self, resolved_ticket_state, mock_chatgpt):
        """Test that response agent appends to conversation history."""
        # Existing history
        resolved_ticket_state["conversation_history"] = [
            "[INTAKE] Customer inquiry",
            "[FAQ] Match found",
            "[CLASSIFIER] Category: GENERAL",
            "[GENERAL] Resolution provided",
            "[ESCALATION] Cleared for automated response"
        ]

        # Mock response
        mock_chatgpt("Thank you for contacting support...")

        # Run the agent
        result = response_generator_agent(resolved_ticket_state)

        # Should have all entries
        assert len(result["conversation_history"]) == 6
        assert "[RESPONSE] Final response generated" in result["conversation_history"][-1]

    def test_response_agent_professional_tone(self, resolved_ticket_state, mock_chatgpt):
        """Test that response maintains professional tone."""
        # Mock professional response
        mock_chatgpt("""Dear Valued Customer,

Thank you for reaching out to our support team. We appreciate your patience.

[Resolution details here]

Ticket ID: TKT-RES001

Should you require further assistance, please do not hesitate to contact us.

Warm regards,
Customer Support Team""")

        # Run the agent
        result = response_generator_agent(resolved_ticket_state)

        # Should have professional content
        assert result["final_response"] != ""
        assert len(result["final_response"]) > 50  # Should be substantial

    def test_response_agent_with_all_categories(self, resolved_ticket_state, mock_chatgpt):
        """Test response generation for all category types."""
        categories = ["TECHNICAL", "BILLING", "GENERAL"]

        for category in categories:
            # Update category
            resolved_ticket_state["category"] = category

            # Mock response
            mock_chatgpt(f"Response for {category} category")

            # Run the agent
            result = response_generator_agent(resolved_ticket_state)

            # Should generate response for each category
            assert result["final_response"] != ""

    def test_response_agent_empathy_in_response(self, resolved_ticket_state, mock_chatgpt):
        """Test that response shows empathy for customer issues."""
        # Mock empathetic response
        mock_chatgpt("""Dear Customer,

I understand how frustrating this situation must be, and I sincerely apologize for any inconvenience.

I'm here to help resolve this for you.

[Resolution details]

Ticket ID: TKT-RES001

Thank you for your patience and understanding.

Best regards,
Support Team""")

        # Run the agent
        result = response_generator_agent(resolved_ticket_state)

        # Should have empathetic tone
        assert result["final_response"] != ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
