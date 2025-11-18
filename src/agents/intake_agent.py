"""
Ticket Intake Agent - First agent in the workflow.
Receives customer queries and extracts key information.
"""

import logging
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.models.state import TicketState
from src.config import config

logger = logging.getLogger(__name__)


def intake_agent(state: TicketState) -> TicketState:
    """
    Process incoming customer query and extract key information.

    Args:
        state: Current ticket state

    Returns:
        Updated state with extracted information
    """
    logger.info(f"Processing ticket intake for: {state['ticket_id']}")

    # Initialize the LLM
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        temperature=config.TEMPERATURE,
        api_key=config.OPENAI_API_KEY
    )

    # Create the intake prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a customer support intake specialist.
        Extract and summarize the key information from customer queries.
        Identify:
        1. Main issue or question
        2. Any product/service mentioned
        3. Urgency level (low, medium, high)
        4. Customer sentiment (positive, neutral, negative)

        Provide a concise summary of the customer's needs."""),
        ("user", "Customer Query: {query}")
    ])

    # Process the query
    chain = prompt | llm
    response = chain.invoke({"query": state["customer_query"]})

    # Update state
    intake_summary = response.content
    state["conversation_history"].append(f"[INTAKE] {intake_summary}")

    # Determine priority based on keywords
    priority = "medium"
    query_lower = state["customer_query"].lower()

    if any(keyword in query_lower for keyword in ["urgent", "critical", "asap", "emergency"]):
        priority = "high"
    elif any(keyword in query_lower for keyword in ["question", "wondering", "curious"]):
        priority = "low"

    state["priority"] = priority
    state["timestamp"] = datetime.now().isoformat()

    logger.info(f"Intake complete - Priority: {priority}")

    return state
