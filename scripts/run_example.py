"""
Example script demonstrating direct usage of the workflow.
Run this script to test the multi-agent system without the API.
"""

import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.workflow import app
from src.config import config
from src.utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def process_ticket(customer_query: str, ticket_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Process a single customer support ticket.

    Args:
        customer_query: The customer's support query
        ticket_id: Optional ticket ID (auto-generated if not provided)
    """
    # Generate ticket ID if not provided
    if not ticket_id:
        ticket_id = f"{config.TICKET_ID_PREFIX}-{uuid.uuid4().hex[:8].upper()}"

    print(f"\n{'='*80}")
    print(f"Processing Ticket: {ticket_id}")
    print(f"{'='*80}")
    print(f"Query: {customer_query}\n")

    # Create initial state
    initial_state = {
        "customer_query": customer_query,
        "ticket_id": ticket_id,
        "category": "",
        "faq_match": "",
        "resolution": "",
        "needs_escalation": False,
        "final_response": "",
        "conversation_history": [],
        "customer_email": "customer@example.com",
        "priority": "medium",
        "timestamp": datetime.now().isoformat(),
        "metadata": {}
    }

    # Process through workflow
    try:
        result = app.invoke(initial_state)

        # Display results
        print(f"Category: {result['category']}")
        print(f"Priority: {result['priority']}")
        print(f"Escalated: {'Yes' if result['needs_escalation'] else 'No'}")
        print(f"\n{'-'*80}")
        print("FINAL RESPONSE:")
        print(f"{'-'*80}")
        print(result['final_response'])
        print(f"\n{'-'*80}")
        print("CONVERSATION HISTORY:")
        print(f"{'-'*80}")
        for entry in result['conversation_history']:
            print(f"  • {entry}")
        print(f"{'='*80}\n")

        return result

    except Exception as e:
        logger.error(f"Error processing ticket: {e}", exc_info=True)
        print(f"Error: {e}")
        return None


def main() -> None:
    """Run example tickets through the system."""
    print("\n" + "="*80)
    print("CUSTOMER SUPPORT MULTI-AGENT SYSTEM - DEMO")
    print("="*80)

    # Validate config
    try:
        config.validate()
    except ValueError as e:
        print(f"\nConfiguration Error: {e}")
        print("Please set OPENAI_API_KEY in your .env file\n")
        return

    # Example tickets
    example_tickets = [
        {
            "query": "My application crashes every time I try to upload files larger than 10MB. I'm using Chrome on Mac.",
            "description": "Technical Issue - File Upload"
        },
        {
            "query": "I was charged twice for my subscription this month. Can I get a refund for the duplicate charge?",
            "description": "Billing Issue - Duplicate Charge"
        },
        {
            "query": "How do I change my email address on my account?",
            "description": "General Inquiry - Account Management"
        },
        {
            "query": "This is completely unacceptable! I've been locked out of my account for 3 days and I'm losing money. I need this fixed immediately or I'll take legal action!",
            "description": "High Priority - Potential Escalation"
        },
    ]

    print(f"\nProcessing {len(example_tickets)} example tickets...\n")

    results = []
    for i, ticket in enumerate(example_tickets, 1):
        print(f"\n{'#'*80}")
        print(f"EXAMPLE {i}: {ticket['description']}")
        print(f"{'#'*80}")

        result = process_ticket(ticket['query'])
        if result:
            results.append(result)

        # Pause between tickets
        if i < len(example_tickets):
            input("\nPress Enter to continue to next ticket...")

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total tickets processed: {len(results)}")
    print(f"Escalated: {sum(1 for r in results if r['needs_escalation'])}")
    print(f"Auto-resolved: {sum(1 for r in results if not r['needs_escalation'])}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
