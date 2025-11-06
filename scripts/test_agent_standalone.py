#!/usr/bin/env python3
"""
Standalone Agent Tester

Test any agent independently with sample data.

Usage:
    python scripts/test_agent_standalone.py intake "My app crashes"
    python scripts/test_agent_standalone.py classifier "I was charged twice"
    python scripts/test_agent_standalone.py technical "App crashing on upload"
    python scripts/test_agent_standalone.py --list
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import agents
from src.agents.intake_agent import intake_agent
from src.agents.faq_agent import faq_lookup_agent
from src.agents.classifier_agent import classifier_agent
from src.agents.technical_agent import technical_support_agent
from src.agents.billing_agent import billing_support_agent
from src.agents.general_agent import general_support_agent
from src.agents.escalation_agent import escalation_evaluator_agent
from src.agents.response_agent import response_generator_agent


# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def create_base_state(query: str, **kwargs) -> Dict[str, Any]:
    """Create a base ticket state."""
    return {
        "customer_query": query,
        "ticket_id": f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "category": kwargs.get("category", ""),
        "faq_match": kwargs.get("faq_match", ""),
        "resolution": kwargs.get("resolution", ""),
        "needs_escalation": False,
        "final_response": "",
        "conversation_history": kwargs.get("conversation_history", []),
        "customer_email": "test@example.com",
        "priority": kwargs.get("priority", "medium"),
        "timestamp": datetime.now().isoformat(),
        "metadata": {}
    }


def print_result(agent_name: str, state_before: Dict, state_after: Dict):
    """Print formatted test results."""
    print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKBLUE}  {agent_name.upper()} AGENT - Test Results{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*70}{Colors.ENDC}\n")

    print(f"{Colors.OKCYAN}Input:{Colors.ENDC}")
    print(f"  Query: {state_before['customer_query']}")
    print(f"  Ticket ID: {state_before['ticket_id']}")
    if state_before.get('category'):
        print(f"  Category: {state_before['category']}")
    if state_before.get('priority'):
        print(f"  Priority: {state_before['priority']}")

    print(f"\n{Colors.OKGREEN}Output:{Colors.ENDC}")

    # Show what changed
    changes = []
    for key in state_after:
        if state_after[key] != state_before.get(key):
            if key == "conversation_history" and len(state_after[key]) > len(state_before.get(key, [])):
                changes.append(("History Added", state_after[key][-1]))
            elif key in ["category", "priority", "faq_match", "resolution", "final_response", "needs_escalation"]:
                if state_after[key]:  # Only show if not empty
                    changes.append((key.replace('_', ' ').title(), state_after[key]))

    for label, value in changes:
        if isinstance(value, bool):
            print(f"  {label}: {value}")
        elif isinstance(value, str):
            if len(value) > 200:
                print(f"  {label}:")
                print(f"    {value[:200]}...")
                print(f"    ... ({len(value)} total characters)")
            else:
                print(f"  {label}: {value}")

    print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}\n")


def test_intake(query: str):
    """Test Intake Agent."""
    state = create_base_state(query)
    state_copy = state.copy()
    result = intake_agent(state)
    print_result("Intake", state_copy, result)
    return result


def test_faq(query: str):
    """Test FAQ Lookup Agent."""
    state = create_base_state(query)
    state_copy = state.copy()
    result = faq_lookup_agent(state)
    print_result("FAQ Lookup", state_copy, result)
    return result


def test_classifier(query: str):
    """Test Classifier Agent."""
    state = create_base_state(query)
    state_copy = state.copy()
    result = classifier_agent(state)
    print_result("Classifier", state_copy, result)
    return result


def test_technical(query: str):
    """Test Technical Support Agent."""
    state = create_base_state(
        query,
        category="TECHNICAL",
        priority="high",
        conversation_history=["[CLASSIFIER] Category: TECHNICAL"]
    )
    state_copy = state.copy()
    result = technical_support_agent(state)
    print_result("Technical Support", state_copy, result)
    return result


def test_billing(query: str):
    """Test Billing Support Agent."""
    state = create_base_state(
        query,
        category="BILLING",
        priority="high",
        conversation_history=["[CLASSIFIER] Category: BILLING"]
    )
    state_copy = state.copy()
    result = billing_support_agent(state)
    print_result("Billing Support", state_copy, result)
    return result


def test_general(query: str):
    """Test General Support Agent."""
    state = create_base_state(
        query,
        category="GENERAL",
        priority="low",
        conversation_history=["[CLASSIFIER] Category: GENERAL"]
    )
    state_copy = state.copy()
    result = general_support_agent(state)
    print_result("General Support", state_copy, result)
    return result


def test_escalation(query: str, with_resolution: bool = True):
    """Test Escalation Evaluator Agent."""
    resolution = "We've reviewed your case and prepared a solution." if with_resolution else ""
    state = create_base_state(
        query,
        category="GENERAL",
        resolution=resolution,
        conversation_history=["[GENERAL] Resolution provided"]
    )
    state_copy = state.copy()
    result = escalation_evaluator_agent(state)
    print_result("Escalation Evaluator", state_copy, result)
    return result


def test_response(query: str):
    """Test Response Generator Agent."""
    state = create_base_state(
        query,
        category="GENERAL",
        resolution="To reset your password:\n1. Go to login page\n2. Click 'Forgot Password'\n3. Follow email instructions",
        conversation_history=[
            "[INTAKE] Customer inquiry",
            "[FAQ] Match found",
            "[CLASSIFIER] Category: GENERAL",
            "[GENERAL] Resolution provided",
            "[ESCALATION] Cleared for automated response"
        ]
    )
    state_copy = state.copy()
    result = response_generator_agent(state)
    print_result("Response Generator", state_copy, result)
    return result


def list_agents():
    """List all available agents."""
    print(f"\n{Colors.HEADER}Available Agents:{Colors.ENDC}\n")

    agents = [
        ("intake", "Ticket Intake Agent", "Extracts key information and sets priority"),
        ("faq", "FAQ Lookup Agent", "Searches knowledge base for matching answers"),
        ("classifier", "Category Classifier Agent", "Categorizes into TECHNICAL/BILLING/GENERAL"),
        ("technical", "Technical Support Agent", "Handles technical issues and troubleshooting"),
        ("billing", "Billing Support Agent", "Handles billing and payment questions"),
        ("general", "General Support Agent", "Handles general inquiries and how-to questions"),
        ("escalation", "Escalation Evaluator Agent", "Determines if human intervention needed"),
        ("response", "Response Generator Agent", "Creates final customer-facing response"),
    ]

    for cmd, name, desc in agents:
        print(f"  {Colors.OKBLUE}{cmd:12}{Colors.ENDC} - {Colors.BOLD}{name}{Colors.ENDC}")
        print(f"                {desc}\n")

    print(f"\n{Colors.OKCYAN}Usage Examples:{Colors.ENDC}")
    print(f"  python scripts/test_agent_standalone.py intake \"My app is crashing\"")
    print(f"  python scripts/test_agent_standalone.py classifier \"I was charged twice\"")
    print(f"  python scripts/test_agent_standalone.py technical \"App crashes on file upload\"")
    print(f"  python scripts/test_agent_standalone.py escalation \"I want to speak to a lawyer!\"")
    print()


def main():
    """Main entry point."""
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print(f"\n{Colors.BOLD}Standalone Agent Tester{Colors.ENDC}")
        print(f"\nTest individual agents with custom queries.\n")
        print(f"{Colors.OKCYAN}Usage:{Colors.ENDC}")
        print(f"  python scripts/test_agent_standalone.py <agent> \"<query>\"")
        print(f"  python scripts/test_agent_standalone.py --list\n")
        list_agents()
        return

    if sys.argv[1] in ["-l", "--list"]:
        list_agents()
        return

    agent = sys.argv[1].lower()
    query = sys.argv[2] if len(sys.argv) > 2 else "Test query"

    # Agent dispatch
    agents = {
        "intake": test_intake,
        "faq": test_faq,
        "classifier": test_classifier,
        "technical": test_technical,
        "billing": test_billing,
        "general": test_general,
        "escalation": test_escalation,
        "response": test_response,
    }

    if agent not in agents:
        print(f"{Colors.FAIL}Error: Unknown agent '{agent}'{Colors.ENDC}")
        print(f"Use --list to see available agents\n")
        return

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print(f"{Colors.WARNING}Warning: OPENAI_API_KEY not set in environment{Colors.ENDC}")
        print(f"Set it with: export OPENAI_API_KEY=sk-your-key-here\n")
        return

    print(f"\n{Colors.BOLD}Testing {agent.upper()} agent...{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Query: {query}{Colors.ENDC}")

    try:
        agents[agent](query)
        print(f"{Colors.OKGREEN}✓ Test completed successfully{Colors.ENDC}\n")
    except Exception as e:
        print(f"\n{Colors.FAIL}✗ Test failed with error:{Colors.ENDC}")
        print(f"{Colors.FAIL}  {str(e)}{Colors.ENDC}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
