"""
LangGraph Workflow - Orchestrates the multi-agent ticket management system.
"""

import logging

from langgraph.graph import StateGraph, END

from src.models.state import TicketState
from src.agents import (
    intake_agent,
    faq_lookup_agent,
    classifier_agent,
    technical_support_agent,
    billing_support_agent,
    general_support_agent,
    escalation_evaluator_agent,
    escalation_response_agent,
    response_generator_agent,
)

logger = logging.getLogger(__name__)


def route_by_category(state: TicketState) -> str:
    """
    Route ticket to appropriate specialized agent based on category.

    Args:
        state: Current ticket state

    Returns:
        Name of the next node to execute
    """
    category = state.get("category", "").strip().upper()

    logger.info(f"Routing ticket {state['ticket_id']} - Category: {category}")

    if "TECHNICAL" in category:
        return "technical_support"
    elif "BILLING" in category:
        return "billing_support"
    else:
        return "general_support"


def handle_escalation(state: TicketState) -> str:
    """
    Route based on escalation decision.

    Args:
        state: Current ticket state

    Returns:
        Name of the next node or END
    """
    if state.get("needs_escalation", False):
        logger.info(f"Ticket {state['ticket_id']} escalated to human agent")
        return "end_escalated"
    else:
        logger.info(f"Ticket {state['ticket_id']} proceeding to automated response")
        return "send_response"


def create_workflow() -> StateGraph:
    """
    Create and configure the LangGraph workflow.

    Workflow structure:
    1. intake -> faq_lookup -> classifier
    2. classifier -> [technical/billing/general] (conditional routing)
    3. specialized_agent -> escalation_check
    4. escalation_check -> [escalation_response/response_gen] (conditional routing)
    5. escalation_response -> END (for escalated tickets)
       response_gen -> END (for auto-resolved tickets)

    Returns:
        Compiled StateGraph application
    """
    logger.info("Creating workflow graph")

    # Initialize the workflow
    workflow = StateGraph(TicketState)

    # Add all agent nodes
    workflow.add_node("intake", intake_agent)
    workflow.add_node("faq_lookup", faq_lookup_agent)
    workflow.add_node("classifier", classifier_agent)
    workflow.add_node("technical_support", technical_support_agent)
    workflow.add_node("billing_support", billing_support_agent)
    workflow.add_node("general_support", general_support_agent)
    workflow.add_node("escalation_check", escalation_evaluator_agent)
    workflow.add_node("escalation_response", escalation_response_agent)
    workflow.add_node("response_gen", response_generator_agent)

    # Define the workflow edges

    # Entry point: Start with intake
    workflow.set_entry_point("intake")

    # Linear flow: intake -> faq_lookup -> classifier
    workflow.add_edge("intake", "faq_lookup")
    workflow.add_edge("faq_lookup", "classifier")

    # Conditional routing by category
    workflow.add_conditional_edges(
        "classifier",
        route_by_category,
        {
            "technical_support": "technical_support",
            "billing_support": "billing_support",
            "general_support": "general_support"
        }
    )

    # All specialized agents lead to escalation check
    workflow.add_edge("technical_support", "escalation_check")
    workflow.add_edge("billing_support", "escalation_check")
    workflow.add_edge("general_support", "escalation_check")

    # Conditional routing based on escalation
    workflow.add_conditional_edges(
        "escalation_check",
        handle_escalation,
        {
            "end_escalated": "escalation_response",
            "send_response": "response_gen"
        }
    )

    # Both response types lead to end
    workflow.add_edge("escalation_response", END)
    workflow.add_edge("response_gen", END)

    logger.info("Workflow graph created successfully")

    # Compile and return the workflow
    return workflow.compile()


# Create the compiled app
app = create_workflow()
