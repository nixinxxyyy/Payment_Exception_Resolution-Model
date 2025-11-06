"""
Tests for the Technical Support Agent.

Tests the agent that handles technical issues and provides troubleshooting.
"""

import pytest
from src.agents.technical_agent import technical_support_agent


class TestTechnicalAgent:
    """Test suite for Technical Support Agent."""

    def test_technical_agent_generates_resolution(self, classified_ticket_state, mock_chatgpt):
        """Test that technical agent generates a resolution."""
        # Mock LLM response with technical resolution
        technical_resolution = """Problem Summary: Application crash during file upload

Troubleshooting Steps:
1. Clear browser cache and cookies
2. Try using a different browser
3. Ensure file size is under 100MB
4. Check internet connection stability

Expected Resolution: Issue should be resolved after following these steps

Additional Notes: If problem persists, we may need to check server logs"""

        mock_chatgpt(technical_resolution)

        # Run the agent
        result = technical_support_agent(classified_ticket_state)

        # Assertions
        assert result["resolution"] != ""
        assert "Problem Summary" in result["resolution"]
        assert "Troubleshooting Steps" in result["resolution"]
        assert len(result["conversation_history"]) == 2  # Original + new entry
        assert "[TECHNICAL] Resolution provided" in result["conversation_history"][-1]

    def test_technical_agent_with_high_priority(self, classified_ticket_state, mock_chatgpt):
        """Test technical agent handles high priority tickets."""
        # Set high priority
        classified_ticket_state["priority"] = "high"

        # Mock resolution
        mock_chatgpt("Critical issue. Immediate troubleshooting required...")

        # Run the agent
        result = technical_support_agent(classified_ticket_state)

        # Should generate resolution
        assert result["resolution"] != ""
        assert result["priority"] == "high"  # Priority preserved

    def test_technical_agent_with_faq_context(self, classified_ticket_state, mock_chatgpt):
        """Test technical agent uses FAQ match as context."""
        # Add FAQ match
        classified_ticket_state["faq_match"] = "Try clearing cache and updating to latest version"

        # Mock resolution incorporating FAQ
        mock_chatgpt("Based on the FAQ, try clearing cache. Additionally, check for system updates.")

        # Run the agent
        result = technical_support_agent(classified_ticket_state)

        # Should have resolution
        assert result["resolution"] != ""

    def test_technical_agent_preserves_state(self, classified_ticket_state, mock_chatgpt):
        """Test that technical agent doesn't modify unrelated state."""
        # Set up state
        classified_ticket_state["ticket_id"] = "TKT-TECH999"
        classified_ticket_state["customer_email"] = "technical@test.com"
        classified_ticket_state["category"] = "TECHNICAL"

        # Mock resolution
        mock_chatgpt("Technical resolution provided")

        # Run the agent
        result = technical_support_agent(classified_ticket_state)

        # These should remain unchanged
        assert result["ticket_id"] == "TKT-TECH999"
        assert result["customer_email"] == "technical@test.com"
        assert result["category"] == "TECHNICAL"

    def test_technical_agent_appends_to_history(self, classified_ticket_state, mock_chatgpt):
        """Test that technical agent appends to conversation history."""
        # Add existing history
        classified_ticket_state["conversation_history"] = [
            "[INTAKE] Customer reports crash",
            "[FAQ] No match found",
            "[CLASSIFIER] Category: TECHNICAL"
        ]

        # Mock resolution
        mock_chatgpt("Follow these troubleshooting steps...")

        # Run the agent
        result = technical_support_agent(classified_ticket_state)

        # Should have all entries
        assert len(result["conversation_history"]) == 4
        assert "[TECHNICAL] Resolution provided" in result["conversation_history"][-1]

    def test_technical_agent_complex_issue(self, classified_ticket_state, mock_chatgpt):
        """Test technical agent with complex technical issue."""
        # Complex query
        classified_ticket_state["customer_query"] = "Application crashes with error code 0x8007000E when uploading files larger than 50MB over VPN connection"

        # Mock detailed resolution
        mock_chatgpt("""Problem Summary: Memory allocation error during large file upload over VPN

Troubleshooting Steps:
1. Increase virtual memory allocation
2. Disable VPN and test direct connection
3. Split large files into smaller chunks
4. Update network drivers

Expected Resolution: VPN may be causing packet fragmentation
Additional Notes: Consider escalation if issue persists""")

        # Run the agent
        result = technical_support_agent(classified_ticket_state)

        # Should provide detailed resolution
        assert result["resolution"] != ""
        assert len(result["resolution"]) > 100  # Should be detailed

    def test_technical_agent_empty_faq_match(self, classified_ticket_state, mock_chatgpt):
        """Test technical agent when no FAQ match exists."""
        # Ensure no FAQ match
        classified_ticket_state["faq_match"] = ""

        # Mock resolution
        mock_chatgpt("Troubleshooting steps provided")

        # Run the agent
        result = technical_support_agent(classified_ticket_state)

        # Should still generate resolution
        assert result["resolution"] != ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
