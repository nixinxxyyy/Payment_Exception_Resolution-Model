"""
Escalation Evaluator Agent - Determines if human intervention is needed.
"""

import logging

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.models.state import TicketState
from src.config import config

logger = logging.getLogger(__name__)


def escalation_evaluator_agent(state: TicketState) -> TicketState:
    """
    Evaluate if the ticket needs human escalation.

    Escalation criteria:
    1. Complex issues requiring human judgment
    2. Legal or compliance matters
    3. High-value refund requests
    4. Frustrated or angry customers
    5. Issues outside the scope of automated resolution

    Args:
        state: Current ticket state

    Returns:
        Updated state with escalation decision
    """
    logger.info(f"Evaluating escalation for ticket: {state['ticket_id']}")

    # Check for automatic escalation keywords
    query_lower = state["customer_query"].lower()
    auto_escalate = any(
        keyword in query_lower
        for keyword in config.ESCALATION_KEYWORDS
    )

    if auto_escalate:
        state["needs_escalation"] = True
        state["conversation_history"].append("[ESCALATION] Auto-escalated based on keywords")
        logger.info("Ticket auto-escalated based on keywords")
        return state

    # Use LLM to evaluate escalation need
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        temperature=0.2,  # Low temperature for consistent decision-making
        openai_api_key=config.OPENAI_API_KEY
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an escalation evaluation specialist.

        Determine if a support ticket needs human escalation based on:

        ESCALATE if:
        - Legal, compliance, or policy violations mentioned
        - Refund requests over $500
        - Customer is clearly frustrated, angry, or threatening
        - Issue requires account-specific access or sensitive data
        - Technical issue appears to be a critical system bug
        - Request involves contract changes or negotiations
        - Complexity beyond automated resolution capability

        DO NOT ESCALATE if:
        - Standard questions answered by FAQ or knowledge base
        - Routine technical troubleshooting
        - Simple billing inquiries
        - General how-to questions
        - Issues with clear documented solutions

        Respond with ONLY one word: ESCALATE or RESOLVE
        No other text or explanation."""),
        ("user", """Customer Query: {query}

        Category: {category}
        Priority: {priority}
        Proposed Resolution: {resolution}

        Decision:""")
    ])

    chain = prompt | llm
    response = chain.invoke({
        "query": state["customer_query"],
        "category": state.get("category", "UNKNOWN"),
        "priority": state.get("priority", "medium"),
        "resolution": state.get("resolution", "")[:500]  # Limit length
    })

    decision = response.content.strip().upper()

    if decision == "ESCALATE":
        state["needs_escalation"] = True
        state["conversation_history"].append("[ESCALATION] Marked for human review")
        logger.info("Ticket marked for escalation")
    else:
        state["needs_escalation"] = False
        state["conversation_history"].append("[ESCALATION] Cleared for automated response")
        logger.info("Ticket cleared for automated response")

    return state
