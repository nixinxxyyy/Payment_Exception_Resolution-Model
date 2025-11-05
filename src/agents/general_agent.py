"""
General Support Agent - Handles general inquiries.
"""

import logging

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.models.state import TicketState
from src.config import config

logger = logging.getLogger(__name__)


def general_support_agent(state: TicketState) -> TicketState:
    """
    Handle general support inquiries.

    Addresses how-to questions, account management, and general information.

    Args:
        state: Current ticket state

    Returns:
        Updated state with general resolution
    """
    logger.info(f"Processing general support for ticket: {state['ticket_id']}")

    # Initialize LLM
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        temperature=config.TEMPERATURE,
        openai_api_key=config.OPENAI_API_KEY
    )

    # Create general support prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a friendly and knowledgeable general support specialist.

        Your role:
        1. Answer general questions about products and services
        2. Provide how-to guidance and best practices
        3. Help with account management questions
        4. Offer helpful resources and documentation
        5. Provide product recommendations when appropriate

        Approach:
        - Be friendly and conversational
        - Provide clear, easy-to-follow instructions
        - Suggest helpful resources or documentation
        - Offer additional assistance if needed

        Format your response with:
        - Direct Answer to Question
        - Step-by-Step Instructions (if applicable)
        - Additional Resources
        - Follow-up Suggestions"""),
        ("user", """Customer Query: {query}

        Priority: {priority}

        FAQ Match: {faq_match}

        Provide general support resolution:""")
    ])

    # Generate general resolution
    chain = prompt | llm
    response = chain.invoke({
        "query": state["customer_query"],
        "priority": state.get("priority", "medium"),
        "faq_match": state.get("faq_match", "None")
    })

    resolution = response.content
    state["resolution"] = resolution
    state["conversation_history"].append(f"[GENERAL] Resolution provided")

    logger.info("General resolution generated")

    return state
