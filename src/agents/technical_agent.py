"""
Technical Support Agent - Handles technical issues.
"""

import logging

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.models.state import TicketState
from src.config import config

logger = logging.getLogger(__name__)


def technical_support_agent(state: TicketState) -> TicketState:
    """
    Handle technical support issues.

    Provides troubleshooting steps, technical solutions, and workarounds.

    Args:
        state: Current ticket state

    Returns:
        Updated state with technical resolution
    """
    logger.info(f"Processing technical support for ticket: {state['ticket_id']}")

    # Initialize LLM
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        temperature=config.TEMPERATURE,
        openai_api_key=config.OPENAI_API_KEY
    )

    # Create technical support prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert technical support specialist.

        Your role:
        1. Analyze technical issues systematically
        2. Provide clear, step-by-step troubleshooting instructions
        3. Offer solutions or workarounds
        4. Explain technical concepts in simple terms
        5. Suggest preventive measures

        If the issue seems complex or requires direct system access, recommend escalation.

        Format your response with:
        - Problem Summary
        - Troubleshooting Steps (numbered)
        - Expected Resolution
        - Additional Notes (if any)"""),
        ("user", """Customer Query: {query}

        Priority: {priority}

        FAQ Match: {faq_match}

        Provide technical support resolution:""")
    ])

    # Generate technical resolution
    chain = prompt | llm
    response = chain.invoke({
        "query": state["customer_query"],
        "priority": state.get("priority", "medium"),
        "faq_match": state.get("faq_match", "None")
    })

    resolution = response.content
    state["resolution"] = resolution
    state["conversation_history"].append(f"[TECHNICAL] Resolution provided")

    logger.info("Technical resolution generated")

    return state
