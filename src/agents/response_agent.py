"""
Response Generator Agent - Creates final customer response.
"""

import logging

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.models.state import TicketState
from src.config import config

logger = logging.getLogger(__name__)


def response_generator_agent(state: TicketState) -> TicketState:
    """
    Generate the final customer-facing response.

    Creates a professional, empathetic response based on the resolution.

    Args:
        state: Current ticket state

    Returns:
        Updated state with final response
    """
    logger.info(f"Generating final response for ticket: {state['ticket_id']}")

    # Initialize LLM
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        temperature=0.7,
        api_key=config.OPENAI_API_KEY
    )

    # Create response generation prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a professional customer support response writer.

        Your task is to create a polished, customer-facing response based on the resolution provided.

        Guidelines:
        1. Start with a warm greeting
        2. Acknowledge the customer's issue with empathy
        3. Provide the solution clearly and concisely
        4. Use a friendly, professional tone
        5. End with an offer for further assistance
        6. Include the ticket ID for reference

        Format:
        - Professional business email format
        - Clear paragraphs
        - Bullet points for steps (if applicable)
        - Signature with support team name

        Avoid:
        - Technical jargon (unless necessary)
        - Overly formal or robotic language
        - Making promises you can't keep
        - Generic template responses"""),
        ("user", """Customer Query: {query}

        Category: {category}
        Ticket ID: {ticket_id}
        Resolution: {resolution}

        Generate final customer response:""")
    ])

    # Generate final response
    chain = prompt | llm
    response = chain.invoke({
        "query": state["customer_query"],
        "category": state.get("category", "GENERAL"),
        "ticket_id": state["ticket_id"],
        "resolution": state.get("resolution", "We're looking into this for you.")
    })

    final_response = response.content
    state["final_response"] = final_response
    state["conversation_history"].append("[RESPONSE] Final response generated")

    logger.info(f"Final response generated for ticket: {state['ticket_id']}")

    return state
