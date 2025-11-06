"""
Tests for the Billing Support Agent.

Tests the agent that handles billing and payment issues.
"""

import pytest
from src.agents.billing_agent import billing_support_agent


class TestBillingAgent:
    """Test suite for Billing Support Agent."""

    def test_billing_agent_generates_resolution(self, billing_ticket_state, mock_chatgpt):
        """Test that billing agent generates a resolution."""
        # Update state to be classified
        billing_ticket_state["category"] = "BILLING"
        billing_ticket_state["conversation_history"] = ["[CLASSIFIER] Category: BILLING"]

        # Mock billing resolution
        billing_resolution = """Issue Acknowledgment: We understand you were charged twice for your subscription

Explanation/Solution: This appears to be a duplicate charge that will be automatically refunded within 3-5 business days

Next Steps:
1. Monitor your account for the refund
2. Contact us if refund not received within 5 days

Policy References: As per our billing policy, duplicate charges are refunded automatically"""

        mock_chatgpt(billing_resolution)

        # Run the agent
        result = billing_support_agent(billing_ticket_state)

        # Assertions
        assert result["resolution"] != ""
        assert "Issue Acknowledgment" in result["resolution"]
        assert "[BILLING] Resolution provided" in result["conversation_history"][-1]

    def test_billing_agent_refund_request(self, billing_ticket_state, mock_chatgpt):
        """Test billing agent handles refund requests."""
        # Refund query
        billing_ticket_state["customer_query"] = "I want a refund for last month's charge"
        billing_ticket_state["category"] = "BILLING"

        # Mock resolution mentioning escalation
        mock_chatgpt("""Issue Acknowledgment: We've received your refund request

Explanation: Refund requests require approval from our billing team

Next Steps: This will be escalated to a billing specialist who will review your request within 24 hours

Policy References: Refund policy section 3.2""")

        # Run the agent
        result = billing_support_agent(billing_ticket_state)

        # Should provide resolution
        assert result["resolution"] != ""

    def test_billing_agent_subscription_question(self, billing_ticket_state, mock_chatgpt):
        """Test billing agent handles subscription questions."""
        # Subscription query
        billing_ticket_state["customer_query"] = "How do I cancel my subscription?"
        billing_ticket_state["category"] = "BILLING"

        # Mock resolution
        mock_chatgpt("""Issue Acknowledgment: You'd like to cancel your subscription

Explanation/Solution: Go to Account Settings > Billing > Cancel Subscription

Next Steps:
1. Navigate to your account settings
2. Select the Billing tab
3. Click 'Cancel Subscription'
4. Confirm cancellation

Policy References: Cancellations are effective at the end of the billing period""")

        # Run the agent
        result = billing_support_agent(billing_ticket_state)

        # Should have detailed steps
        assert result["resolution"] != ""
        assert len(result["resolution"]) > 50

    def test_billing_agent_with_priority(self, billing_ticket_state, mock_chatgpt):
        """Test billing agent respects priority levels."""
        # Set high priority
        billing_ticket_state["priority"] = "high"
        billing_ticket_state["category"] = "BILLING"

        # Mock resolution
        mock_chatgpt("High priority billing issue addressed immediately...")

        # Run the agent
        result = billing_support_agent(billing_ticket_state)

        # Priority should be preserved
        assert result["priority"] == "high"
        assert result["resolution"] != ""

    def test_billing_agent_preserves_state(self, billing_ticket_state, mock_chatgpt):
        """Test that billing agent doesn't modify unrelated state."""
        # Set up state
        billing_ticket_state["ticket_id"] = "TKT-BILL999"
        billing_ticket_state["customer_email"] = "billing@test.com"
        billing_ticket_state["category"] = "BILLING"
        billing_ticket_state["metadata"] = {"amount": 99.99}

        # Mock resolution
        mock_chatgpt("Billing resolution provided")

        # Run the agent
        result = billing_support_agent(billing_ticket_state)

        # These should remain unchanged
        assert result["ticket_id"] == "TKT-BILL999"
        assert result["customer_email"] == "billing@test.com"
        assert result["category"] == "BILLING"
        assert result["metadata"]["amount"] == 99.99

    def test_billing_agent_with_faq_context(self, billing_ticket_state, mock_chatgpt):
        """Test billing agent uses FAQ match as context."""
        # Add FAQ match
        billing_ticket_state["faq_match"] = "You will be charged on the same day each month"
        billing_ticket_state["category"] = "BILLING"

        # Mock resolution incorporating FAQ
        mock_chatgpt("Based on our billing policy, you are charged monthly on your signup date.")

        # Run the agent
        result = billing_support_agent(billing_ticket_state)

        # Should have resolution
        assert result["resolution"] != ""

    def test_billing_agent_payment_issue(self, billing_ticket_state, mock_chatgpt):
        """Test billing agent handles payment issues."""
        # Payment failure query
        billing_ticket_state["customer_query"] = "My payment failed but I have sufficient funds"
        billing_ticket_state["category"] = "BILLING"

        # Mock resolution
        mock_chatgpt("""Issue Acknowledgment: Your payment was declined despite sufficient funds

Explanation: This could be due to:
- Bank security measures
- Expired card information
- International transaction blocks

Next Steps:
1. Contact your bank to authorize the transaction
2. Update payment method in your account
3. Retry the payment

Policy References: Payment troubleshooting guide""")

        # Run the agent
        result = billing_support_agent(billing_ticket_state)

        # Should provide troubleshooting
        assert result["resolution"] != ""

    def test_billing_agent_invoice_request(self, billing_ticket_state, mock_chatgpt):
        """Test billing agent handles invoice requests."""
        billing_ticket_state["customer_query"] = "I need an invoice for last month"
        billing_ticket_state["category"] = "BILLING"

        # Mock resolution
        mock_chatgpt("""Issue Acknowledgment: You need an invoice for your recent payment

Next Steps:
1. Go to Account Settings > Billing > Invoices
2. Select the invoice date
3. Download PDF

If you need help, we can email it to you directly.""")

        # Run the agent
        result = billing_support_agent(billing_ticket_state)

        # Should provide clear instructions
        assert result["resolution"] != ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
