"""
Tests for the FAQ Lookup Agent.

Tests the agent that searches the knowledge base for matching FAQs.
"""

import pytest
import json
import os
from unittest.mock import patch, mock_open
from src.agents.faq_agent import faq_lookup_agent, load_faq_database


class TestFAQAgent:
    """Test suite for FAQ Lookup Agent."""

    def test_faq_agent_finds_match(self, general_ticket_state, mock_chatgpt, sample_faq_database, monkeypatch):
        """Test that FAQ agent finds a matching answer."""
        # Mock the FAQ database loading
        monkeypatch.setattr(
            "src.agents.faq_agent.load_faq_database",
            lambda: sample_faq_database
        )

        # Mock LLM to return a matched FAQ
        mock_chatgpt("Click 'Forgot Password' on the login page and follow the instructions.")

        # Run the agent
        result = faq_lookup_agent(general_ticket_state)

        # Assertions
        assert result["faq_match"] != ""
        assert "Click 'Forgot Password'" in result["faq_match"]
        assert len(result["conversation_history"]) == 1
        assert "[FAQ] Match found" in result["conversation_history"][0]

    def test_faq_agent_no_match(self, technical_ticket_state, mock_chatgpt, sample_faq_database, monkeypatch):
        """Test that FAQ agent handles no match scenario."""
        # Mock the FAQ database loading
        monkeypatch.setattr(
            "src.agents.faq_agent.load_faq_database",
            lambda: sample_faq_database
        )

        # Mock LLM to return NO_MATCH
        mock_chatgpt("NO_MATCH")

        # Run the agent
        result = faq_lookup_agent(technical_ticket_state)

        # Assertions
        assert result["faq_match"] == ""
        assert "[FAQ] No direct match found" in result["conversation_history"][0]

    def test_faq_agent_empty_database(self, base_ticket_state, mock_chatgpt, monkeypatch):
        """Test FAQ agent behavior with empty database."""
        # Mock empty FAQ database
        monkeypatch.setattr(
            "src.agents.faq_agent.load_faq_database",
            lambda: {"faqs": []}
        )

        # Run the agent
        result = faq_lookup_agent(base_ticket_state)

        # Assertions
        assert result["faq_match"] == "No FAQ entries available"
        assert "[FAQ] No FAQ database found" in result["conversation_history"][0]

    def test_faq_agent_preserves_other_state(self, general_ticket_state, mock_chatgpt, sample_faq_database, monkeypatch):
        """Test that FAQ agent doesn't modify unrelated state fields."""
        # Set up some state
        general_ticket_state["priority"] = "high"
        general_ticket_state["metadata"] = {"source": "email"}

        # Mock the FAQ database
        monkeypatch.setattr(
            "src.agents.faq_agent.load_faq_database",
            lambda: sample_faq_database
        )

        # Mock LLM response
        mock_chatgpt("Click 'Forgot Password' on the login page.")

        # Run the agent
        result = faq_lookup_agent(general_ticket_state)

        # These should remain unchanged
        assert result["priority"] == "high"
        assert result["metadata"]["source"] == "email"
        assert result["ticket_id"] == "TKT-GEN001"

    def test_load_faq_database_success(self, sample_faq_database, monkeypatch):
        """Test successful FAQ database loading."""
        # Mock file operations
        mock_file_content = json.dumps(sample_faq_database)
        mock_file = mock_open(read_data=mock_file_content)

        with patch("builtins.open", mock_file):
            with patch("os.path.exists", return_value=True):
                result = load_faq_database()

        # Assertions
        assert "faqs" in result
        assert len(result["faqs"]) == 5
        assert result["faqs"][0]["question"] == "How do I reset my password?"

    def test_load_faq_database_file_not_found(self, monkeypatch):
        """Test FAQ database loading when file doesn't exist."""
        with patch("os.path.exists", return_value=False):
            result = load_faq_database()

        # Should return empty database
        assert result == {"faqs": []}

    def test_load_faq_database_invalid_json(self, monkeypatch):
        """Test FAQ database loading with invalid JSON."""
        # Mock file with invalid JSON
        mock_file = mock_open(read_data="invalid json {")

        with patch("builtins.open", mock_file):
            with patch("os.path.exists", return_value=True):
                result = load_faq_database()

        # Should return empty database on error
        assert result == {"faqs": []}

    def test_faq_agent_conversation_history_append(self, general_ticket_state, mock_chatgpt, sample_faq_database, monkeypatch):
        """Test that FAQ agent appends to conversation history."""
        # Add existing history
        general_ticket_state["conversation_history"] = ["[INTAKE] Customer asking about password"]

        # Mock the FAQ database
        monkeypatch.setattr(
            "src.agents.faq_agent.load_faq_database",
            lambda: sample_faq_database
        )

        # Mock LLM response
        mock_chatgpt("Click 'Forgot Password' on the login page.")

        # Run the agent
        result = faq_lookup_agent(general_ticket_state)

        # Should have both entries
        assert len(result["conversation_history"]) == 2
        assert "[INTAKE]" in result["conversation_history"][0]
        assert "[FAQ]" in result["conversation_history"][1]

    def test_faq_agent_truncates_long_match_in_history(self, general_ticket_state, mock_chatgpt, sample_faq_database, monkeypatch):
        """Test that very long FAQ matches are truncated in conversation history."""
        # Mock the FAQ database
        monkeypatch.setattr(
            "src.agents.faq_agent.load_faq_database",
            lambda: sample_faq_database
        )

        # Mock a very long FAQ response
        long_response = "A" * 200  # 200 characters
        mock_chatgpt(long_response)

        # Run the agent
        result = faq_lookup_agent(general_ticket_state)

        # Full match should be stored
        assert len(result["faq_match"]) == 200

        # But conversation history should be truncated to 100 chars
        history_entry = result["conversation_history"][0]
        # Extract just the match part (after "[FAQ] Match found: ")
        assert "..." in history_entry  # Truncation indicator


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
