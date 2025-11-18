"""
FAQ Lookup Agent - Searches knowledge base for quick resolutions.
"""

import json
import logging
import os
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.models.state import TicketState
from src.config import config

logger = logging.getLogger(__name__)


def load_faq_database() -> Dict[str, Any]:
    """Load FAQ database from file."""
    try:
        if os.path.exists(config.FAQ_DATABASE_PATH):
            with open(config.FAQ_DATABASE_PATH, 'r') as f:
                return json.load(f)
        else:
            logger.warning("FAQ database not found, using empty database")
            return {"faqs": []}
    except Exception as e:
        logger.error(f"Error loading FAQ database: {e}")
        return {"faqs": []}


def faq_lookup_agent(state: TicketState) -> TicketState:
    """
    Search FAQ database for matching solutions.

    Args:
        state: Current ticket state

    Returns:
        Updated state with FAQ match if found
    """
    logger.info(f"Searching FAQ for ticket: {state['ticket_id']}")

    # Load FAQ database
    faq_db = load_faq_database()

    # Initialize LLM for semantic search
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        temperature=0.3,  # Lower temperature for more deterministic matching
        api_key=config.OPENAI_API_KEY
    )

    # Create FAQ search prompt
    faq_list = "\n".join([
        f"Q: {faq['question']}\nA: {faq['answer']}"
        for faq in faq_db.get("faqs", [])
    ])

    if not faq_list:
        state["faq_match"] = "No FAQ entries available"
        state["conversation_history"].append("[FAQ] No FAQ database found")
        return state

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a FAQ matching specialist.
        Given a customer query and a list of FAQ entries, determine if any FAQ directly addresses the customer's question.
        If you find a match, return ONLY the answer from the FAQ.
        If no good match exists, respond with 'NO_MATCH'.
        Be strict - only return a match if it directly addresses the query."""),
        ("user", """Customer Query: {query}

Available FAQs:
{faq_list}

Your response:""")
    ])

    # Search for matching FAQ
    chain = prompt | llm
    response = chain.invoke({
        "query": state["customer_query"],
        "faq_list": faq_list
    })

    faq_match = response.content.strip()

    if faq_match != "NO_MATCH":
        state["faq_match"] = faq_match
        state["conversation_history"].append(f"[FAQ] Match found: {faq_match[:100]}...")
        logger.info("FAQ match found")
    else:
        state["faq_match"] = ""
        state["conversation_history"].append("[FAQ] No direct match found")
        logger.info("No FAQ match found")

    return state
