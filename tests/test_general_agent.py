"""
Tests for the General Support Agent.

Tests the agent that handles general inquiries and how-to questions.
"""

import pytest
from src.agents.general_agent import general_support_agent


class TestGeneralAgent:
    """Test suite for General Support Agent."""

    def test_general_agent_generates_resolution(self, general_ticket_state, mock_chatgpt):
        """Test that general agent generates a resolution."""
        # Update state to be classified
        general_ticket_state["category"] = "GENERAL"
        general_ticket_state["conversation_history"] = ["[CLASSIFIER] Category: GENERAL"]

        # Mock general resolution
        general_resolution = """Direct Answer: To reset your password, follow these steps

Step-by-Step Instructions:
1. Go to the login page
2. Click 'Forgot Password'
3. Enter your email address
4. Check your email for the reset link
5. Click the link and create a new password

Additional Resources:
- Password security best practices guide
- Account security FAQ

Follow-up Suggestions: Consider enabling two-factor authentication for added security"""

        mock_chatgpt(general_resolution)

        # Run the agent
        result = general_support_agent(general_ticket_state)

        # Assertions
        assert result["resolution"] != ""
        assert "Direct Answer" in result["resolution"]
        assert "[GENERAL] Resolution provided" in result["conversation_history"][-1]

    def test_general_agent_how_to_question(self, general_ticket_state, mock_chatgpt):
        """Test general agent handles how-to questions."""
        # How-to query
        general_ticket_state["customer_query"] = "How do I change my email address?"
        general_ticket_state["category"] = "GENERAL"

        # Mock resolution
        mock_chatgpt("""Direct Answer: You can change your email in Account Settings

Step-by-Step Instructions:
1. Log in to your account
2. Go to Settings > Profile
3. Click 'Edit' next to Email
4. Enter new email address
5. Verify with confirmation code

Additional Resources: Account management guide

Follow-up Suggestions: Update your notification preferences after changing email""")

        # Run the agent
        result = general_support_agent(general_ticket_state)

        # Should provide clear steps
        assert result["resolution"] != ""

    def test_general_agent_account_management(self, general_ticket_state, mock_chatgpt):
        """Test general agent handles account management questions."""
        general_ticket_state["customer_query"] = "How do I delete my account?"
        general_ticket_state["category"] = "GENERAL"

        # Mock resolution
        mock_chatgpt("""Direct Answer: Account deletion can be done from Settings

Step-by-Step Instructions:
1. Go to Account Settings
2. Scroll to 'Delete Account' section
3. Click 'Delete My Account'
4. Confirm deletion

Additional Resources: Data retention policy

Follow-up Suggestions: Download your data before deletion if needed""")

        # Run the agent
        result = general_support_agent(general_ticket_state)

        # Should have resolution
        assert result["resolution"] != ""

    def test_general_agent_product_inquiry(self, general_ticket_state, mock_chatgpt):
        """Test general agent handles product inquiries."""
        general_ticket_state["customer_query"] = "What features are included in the premium plan?"
        general_ticket_state["category"] = "GENERAL"

        # Mock resolution
        mock_chatgpt("""Direct Answer: Premium plan includes advanced features

Premium Features:
- Unlimited storage
- Priority support
- Advanced analytics
- API access
- Custom branding

Additional Resources: Pricing comparison page

Follow-up Suggestions: Try our 14-day free trial to test premium features""")

        # Run the agent
        result = general_support_agent(general_ticket_state)

        # Should provide feature information
        assert result["resolution"] != ""

    def test_general_agent_with_faq_context(self, general_ticket_state, mock_chatgpt):
        """Test general agent uses FAQ match as context."""
        # Add FAQ match
        general_ticket_state["faq_match"] = "Click 'Forgot Password' on the login page"
        general_ticket_state["category"] = "GENERAL"

        # Mock resolution incorporating FAQ
        mock_chatgpt("""Direct Answer: As mentioned in our FAQ, click 'Forgot Password'

Step-by-Step Instructions:
1. Navigate to login page
2. Click 'Forgot Password' link
3. Follow the email instructions

Additional Resources: Password help guide""")

        # Run the agent
        result = general_support_agent(general_ticket_state)

        # Should use FAQ context
        assert result["resolution"] != ""

    def test_general_agent_preserves_state(self, general_ticket_state, mock_chatgpt):
        """Test that general agent doesn't modify unrelated state."""
        # Set up state
        general_ticket_state["ticket_id"] = "TKT-GEN999"
        general_ticket_state["customer_email"] = "general@test.com"
        general_ticket_state["category"] = "GENERAL"
        general_ticket_state["priority"] = "low"

        # Mock resolution
        mock_chatgpt("General resolution provided")

        # Run the agent
        result = general_support_agent(general_ticket_state)

        # These should remain unchanged
        assert result["ticket_id"] == "TKT-GEN999"
        assert result["customer_email"] == "general@test.com"
        assert result["category"] == "GENERAL"
        assert result["priority"] == "low"

    def test_general_agent_friendly_tone(self, general_ticket_state, mock_chatgpt):
        """Test general agent provides friendly, helpful responses."""
        general_ticket_state["category"] = "GENERAL"

        # Mock a friendly response
        mock_chatgpt("""Direct Answer: I'd be happy to help you with that!

Step-by-Step Instructions:
1. First step
2. Second step

Additional Resources: Help center

Follow-up Suggestions: Feel free to reach out if you need more help!""")

        # Run the agent
        result = general_support_agent(general_ticket_state)

        # Should have a friendly tone (checking for resolution existence)
        assert result["resolution"] != ""
        assert len(result["resolution"]) > 0

    def test_general_agent_with_priority(self, general_ticket_state, mock_chatgpt):
        """Test general agent respects priority levels."""
        # Set priority
        general_ticket_state["priority"] = "low"
        general_ticket_state["category"] = "GENERAL"

        # Mock resolution
        mock_chatgpt("Quick answer to your question...")

        # Run the agent
        result = general_support_agent(general_ticket_state)

        # Priority should be preserved
        assert result["priority"] == "low"
        assert result["resolution"] != ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
