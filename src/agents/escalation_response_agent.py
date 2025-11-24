"""
Escalation Response Agent - Creates customer-facing response for escalated tickets.
"""

import logging

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.models.state import TicketState
from src.config import config

logger = logging.getLogger(__name__)


def escalation_response_agent(state: TicketState) -> TicketState:
    """
    Generate a professional, empathetic response for escalated tickets.

    Creates a customer-facing message that:
    - Acknowledges the issue with empathy
    - Explains that the ticket is being escalated
    - Sets clear expectations for human follow-up
    - Maintains a professional and reassuring tone

    Args:
        state: Current ticket state

    Returns:
        Updated state with final_response for escalated ticket
    """
    logger.info(f"Generating escalation response for ticket: {state['ticket_id']}")

    # Initialize LLM with higher temperature for more empathetic responses
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        temperature=0.7,
        api_key=config.OPENAI_API_KEY
    )

    # Create escalation response prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a professional customer support specialist writing escalation notifications.

        Your task is to create a warm, empathetic message informing the customer their ticket is being escalated to a human specialist.

        Guidelines:
        1. Start with a warm, personalized greeting
        2. Acknowledge their specific issue with genuine empathy
        3. Explain why escalation is beneficial (without making it sound negative)
        4. Clearly state that a human specialist will handle their case
        5. Set realistic expectations for response time (within 24 hours)
        6. Express appreciation for their patience
        7. Include the ticket ID for reference
        8. End with reassurance that their issue is important

        Tone:
        - Empathetic and understanding
        - Professional but warm
        - Reassuring and confident
        - Personalized to their specific issue

        Avoid:
        - Making it sound like a failure or problem
        - Generic template language
        - Overpromising on resolution
        - Defensive or apologetic tone
        - Technical jargon

        Format as a professional email response."""),
        ("user", """Customer Query: {query}

        Category: {category}
        Priority: {priority}
        Ticket ID: {ticket_id}
        Internal Resolution Notes: {resolution}

        Generate an empathetic escalation notification:""")
    ])

    # Generate escalation response
    chain = prompt | llm
    response = chain.invoke({
        "query": state["customer_query"],
        "category": state.get("category", "GENERAL"),
        "priority": state.get("priority", "medium"),
        "ticket_id": state["ticket_id"],
        "resolution": state.get("resolution", "Requires specialized review")
    })

    final_response = response.content
    state["final_response"] = final_response
    state["conversation_history"].append("[ESCALATION RESPONSE] Customer notification generated")

    logger.info(f"Escalation response generated for ticket: {state['ticket_id']}")

    return state
