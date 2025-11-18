"""
Category Classifier Agent - Determines issue type.
Routes to appropriate specialized agent.
"""

import logging

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.models.state import TicketState, TicketCategory
from src.config import config

logger = logging.getLogger(__name__)


def classifier_agent(state: TicketState) -> TicketState:
    """
    Classify the ticket into appropriate category.

    Categories:
    - TECHNICAL: Software bugs, technical issues, system errors
    - BILLING: Payment, invoices, subscriptions, refunds
    - GENERAL: General inquiries, how-to questions, account management

    Args:
        state: Current ticket state

    Returns:
        Updated state with category classification
    """
    logger.info(f"Classifying ticket: {state['ticket_id']}")

    # Initialize LLM
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        temperature=0.1,  # Very low temperature for consistent classification
        api_key=config.OPENAI_API_KEY
    )

    # Create classification prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a support ticket classifier.
        Classify customer queries into EXACTLY ONE of these categories:

        1. TECHNICAL - Software issues, bugs, errors, crashes, performance problems, technical difficulties
        2. BILLING - Payments, invoices, subscriptions, pricing, refunds, charges, billing questions
        3. GENERAL - Account questions, how-to queries, general information, product inquiries

        Respond with ONLY the category name: TECHNICAL, BILLING, or GENERAL.
        No other text or explanation."""),
        ("user", """Customer Query: {query}

        FAQ Match (if any): {faq_match}

        Classification:""")
    ])

    # Classify the ticket
    chain = prompt | llm
    response = chain.invoke({
        "query": state["customer_query"],
        "faq_match": state.get("faq_match", "")
    })

    # Extract and validate category
    category = response.content.strip().upper()

    # Validate category
    valid_categories = [cat.value for cat in TicketCategory]
    if category not in valid_categories:
        logger.warning(f"Invalid category '{category}', defaulting to GENERAL")
        category = TicketCategory.GENERAL.value

    state["category"] = category
    state["conversation_history"].append(f"[CLASSIFIER] Category: {category}")

    logger.info(f"Ticket classified as: {category}")

    return state
