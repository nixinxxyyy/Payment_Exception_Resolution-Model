"""
Billing Support Agent - Handles billing and payment issues.
"""

import logging

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.models.state import TicketState
from src.config import config

logger = logging.getLogger(__name__)


def billing_support_agent(state: TicketState) -> TicketState:
    """
    Handle billing and payment related issues.

    Addresses payments, refunds, subscriptions, invoices, and pricing.

    Args:
        state: Current ticket state

    Returns:
        Updated state with billing resolution
    """
    logger.info(f"Processing billing support for ticket: {state['ticket_id']}")

    # Initialize LLM
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        temperature=config.TEMPERATURE,
        api_key=config.OPENAI_API_KEY
    )

    # Create billing support prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a billing and payment support specialist.

        Your role:
        1. Address billing questions clearly and professionally
        2. Explain payment processes and policies
        3. Provide information about refunds, credits, and adjustments
        4. Clarify subscription details and pricing
        5. Handle invoice and receipt requests

        Important notes:
        - Be empathetic with billing complaints
        - Clearly explain any charges or fees
        - For refund requests or disputes, recommend escalation for approval
        - Provide account-specific details when possible

        Format your response with:
        - Issue Acknowledgment
        - Explanation/Solution
        - Next Steps
        - Policy References (if applicable)"""),
        ("user", """Customer Query: {query}

        Priority: {priority}

        FAQ Match: {faq_match}

        Provide billing support resolution:""")
    ])

    # Generate billing resolution
    chain = prompt | llm
    response = chain.invoke({
        "query": state["customer_query"],
        "priority": state.get("priority", "medium"),
        "faq_match": state.get("faq_match", "None")
    })

    resolution = response.content
    state["resolution"] = resolution
    state["conversation_history"].append(f"[BILLING] Resolution provided")

    logger.info("Billing resolution generated")

    return state
