"""
LangGraph Workflow — Orchestrates the Payment Exception Resolution multi-agent system.

Workflow structure:
  ingestion
    ↓
  investigation
    ↓
  root_cause_analysis
    ↓
  decision
    ↓ (conditional routing on resolution_action)
  ┌──────────────────────────────────────────────────────────┐
  │ AUTO_RETRY / AUTO_CORRECT /   │ CLIENT_OUTREACH          │
  │ DUPLICATE_SUPPRESS /          │                          │
  │ HOLD_FOR_WINDOW               │                          │
  │         ↓                     │           ↓              │
  │   auto_resolve                │   client_outreach        │
  │                               │                          │
  │ COMPLIANCE_REVIEW             │ MANUAL_REVIEW /          │
  │         ↓                     │ CANCEL                   │
  │   compliance_escalation       │           ↓              │
  │                               │   manual_review          │
  └──────────────────────────────────────────────────────────┘
                    ↓ (all paths converge)
                  egress
                    ↓
                   END
"""

import logging

from langgraph.graph import StateGraph, END

from src.models.state import (
    PaymentExceptionState,
    ResolutionAction,
    ExceptionStatus,
)
from src.agents import (
    ingestion_agent,
    investigation_agent,
    root_cause_agent,
    decision_agent,
    auto_resolve_agent,
    client_outreach_agent,
    compliance_agent,
    manual_review_agent,
    egress_agent,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Routing functions
# ---------------------------------------------------------------------------

def route_after_decision(state: PaymentExceptionState) -> str:
    """
    Route to the appropriate execution node based on the resolution_action.
    """
    action = state.get("resolution_action", ResolutionAction.MANUAL_REVIEW.value)

    logger.info(
        f"[Workflow] Routing exception {state['exception_id']} "
        f"with action={action}"
    )

    auto_actions = {
        ResolutionAction.AUTO_RETRY.value,
        ResolutionAction.AUTO_CORRECT.value,
        ResolutionAction.DUPLICATE_SUPPRESS.value,
        ResolutionAction.HOLD_FOR_WINDOW.value,
    }

    if action in auto_actions:
        return "auto_resolve"
    elif action == ResolutionAction.CLIENT_OUTREACH.value:
        return "client_outreach"
    elif action == ResolutionAction.COMPLIANCE_REVIEW.value:
        return "compliance_escalation"
    else:
        # MANUAL_REVIEW, CANCEL, or any unknown action
        return "manual_review"


def route_after_ingestion(state: PaymentExceptionState) -> str:
    """
    Short-circuit if this is a duplicate event that has already been handled.
    """
    if state.get("is_duplicate_event") and state.get("metadata", {}).get("duplicate_suppressed"):
        logger.info(
            f"[Workflow] Duplicate event for {state['exception_id']} — "
            "routing directly to egress."
        )
        return "egress"
    return "investigation"


# ---------------------------------------------------------------------------
# Workflow factory
# ---------------------------------------------------------------------------

def create_workflow() -> StateGraph:
    """
    Build and compile the LangGraph StateGraph for payment exception resolution.

    Returns:
        Compiled StateGraph application ready to invoke.
    """
    logger.info("[Workflow] Building payment exception resolution graph...")

    workflow = StateGraph(PaymentExceptionState)

    # ------------------------------------------------------------------
    # Register nodes
    # ------------------------------------------------------------------
    workflow.add_node("ingestion",            ingestion_agent)
    workflow.add_node("investigation",        investigation_agent)
    workflow.add_node("root_cause_analysis",  root_cause_agent)
    workflow.add_node("decision",             decision_agent)
    workflow.add_node("auto_resolve",         auto_resolve_agent)
    workflow.add_node("client_outreach",      client_outreach_agent)
    workflow.add_node("compliance_escalation", compliance_agent)
    workflow.add_node("manual_review",        manual_review_agent)
    workflow.add_node("egress",               egress_agent)

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------
    workflow.set_entry_point("ingestion")

    # ------------------------------------------------------------------
    # Edges
    # ------------------------------------------------------------------

    # After ingestion: check for duplicate events
    workflow.add_conditional_edges(
        "ingestion",
        route_after_ingestion,
        {
            "investigation": "investigation",
            "egress":        "egress",
        }
    )

    # Linear investigation → root cause → decision
    workflow.add_edge("investigation",       "root_cause_analysis")
    workflow.add_edge("root_cause_analysis", "decision")

    # Decision fans out to execution nodes
    workflow.add_conditional_edges(
        "decision",
        route_after_decision,
        {
            "auto_resolve":         "auto_resolve",
            "client_outreach":      "client_outreach",
            "compliance_escalation": "compliance_escalation",
            "manual_review":        "manual_review",
        }
    )

    # All execution nodes converge to egress
    workflow.add_edge("auto_resolve",          "egress")
    workflow.add_edge("client_outreach",       "egress")
    workflow.add_edge("compliance_escalation", "egress")
    workflow.add_edge("manual_review",         "egress")

    # Egress → END
    workflow.add_edge("egress", END)

    logger.info("[Workflow] Graph built successfully.")

    return workflow.compile()


# Compiled application — imported by the API layer
app = create_workflow()
