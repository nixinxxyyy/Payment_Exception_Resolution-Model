"""
Manual Review Agent — Packages uncertain cases for operations team review.

Handles: MANUAL_REVIEW (and any action that cannot be safely automated)

Responsibilities:
  1. Build a complete case dossier for the ops analyst
  2. Assign priority tier based on amount, retries, and failure type
  3. Route to the correct ops queue
  4. Lock the payment from further automated action
  5. Set case SLA deadline
"""

import logging
from datetime import datetime, timedelta

from src.models.state import (
    PaymentExceptionState,
    FailureType,
    ExceptionStatus,
)
from src.config import config

logger = logging.getLogger(__name__)


def _make_audit(action: str, evidence: list, decision: str, justification: str) -> dict:
    return {
        "agent": "manual_review_agent",
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "evidence_used": evidence,
        "decision": decision,
        "justification": justification,
    }


def _determine_priority_and_queue(
    failure_type: str,
    amount: float,
    retry_count: int,
    compliance_flags: list,
) -> tuple[str, str, int]:
    """
    Returns (priority: P1/P2/P3, queue: str, sla_hours: int).
    """
    if compliance_flags:
        return "P1", "COMPLIANCE_OPS_QUEUE", 4

    if amount >= config.HIGH_VALUE_THRESHOLD:
        return "P1", "HIGH_VALUE_OPS_QUEUE", 4

    if failure_type == FailureType.UNCERTAIN_RETRY_STATUS.value:
        return "P1", "RETRY_INVESTIGATION_QUEUE", 2

    if retry_count >= config.MAX_RETRY_ATTEMPTS:
        return "P2", "EXHAUSTED_RETRY_QUEUE", 8

    if failure_type == FailureType.NETWORK_RAIL_FAILURE.value:
        return "P2", "NETWORK_EXCEPTION_QUEUE", 8

    return "P3", "GENERAL_OPS_QUEUE", 24


def manual_review_agent(state: PaymentExceptionState) -> PaymentExceptionState:
    """
    Package the exception case for operations team review.

    Mutates: escalation_queue, execution_result, status → ESCALATED
    """
    logger.info(f"[ManualReviewAgent] Packaging case {state['exception_id']}")

    failure_type = state.get("failure_type", FailureType.UNKNOWN.value)
    amount       = state.get("amount", 0)
    retries      = state.get("retry_count", 0)
    flags        = state.get("compliance_flags") or []

    priority, queue, sla_hours = _determine_priority_and_queue(
        failure_type, amount, retries, flags
    )

    sla_deadline = (datetime.utcnow() + timedelta(hours=sla_hours)).isoformat()

    ben = state.get("beneficiary_details") or {}
    net = state.get("network_status") or {}
    bal = state.get("balance_check") or {}

    # Build the ops dossier
    dossier = {
        "exception_id":    state.get("exception_id"),
        "payment_id":      state.get("payment_id"),
        "client_id":       state.get("client_id"),
        "account_id":      state.get("account_id"),
        "amount":          f"{state.get('currency', 'INR')} {amount:,.2f}",
        "payment_rail":    state.get("payment_rail"),
        "payment_type":    state.get("payment_type"),
        "failure_type":    failure_type,
        "failure_code":    state.get("failure_code"),
        "failure_message": state.get("failure_message"),
        "root_cause":      state.get("root_cause_summary"),
        "decision_confidence": state.get("decision_confidence", 0),
        "retry_count":     retries,
        "max_retries":     state.get("max_retries_allowed", config.MAX_RETRY_ATTEMPTS),
        "beneficiary": {
            "account_no": ben.get("account_no", "N/A"),
            "ifsc":       ben.get("ifsc", ben.get("bic", "N/A")),
            "name":       ben.get("name", "N/A"),
            "upi_id":     ben.get("upi_id", "N/A"),
        },
        "network_status":  net.get("status", "UNKNOWN"),
        "balance": {
            "available": bal.get("available", "N/A"),
            "required":  bal.get("required", amount),
            "sufficient": bal.get("sufficient", "unknown"),
        },
        "compliance_flags":  flags or "none",
        "prior_retries":     state.get("prior_retry_records", []),
        "audit_trail_length": len(state.get("audit_trail", [])),
        "submitted_at":      state.get("submitted_at"),
        "priority":          priority,
        "queue":             queue,
        "sla_deadline":      sla_deadline,
        "assigned_to":       f"{queue} (auto-assigned)",
    }

    state["escalation_queue"] = queue
    state["execution_result"] = {
        "outcome":        "QUEUED_FOR_MANUAL_REVIEW",
        "priority":       priority,
        "queue":          queue,
        "sla_deadline":   sla_deadline,
        "dossier":        dossier,
        "payment_locked": True,
        "note": (
            f"Exception {state['exception_id']} queued for manual review. "
            f"Priority: {priority}. SLA: {sla_hours}h. Queue: {queue}. (stubbed)"
        ),
    }
    state["status"] = ExceptionStatus.ESCALATED.value

    # Client message (generic, non-alarmist)
    state["client_message"] = (
        f"Dear Valued Customer,\n\n"
        f"Your payment of {state.get('currency', 'INR')} {amount:,.2f} "
        f"(Reference: {state.get('payment_id', 'N/A')}) requires additional "
        f"review by our operations team.\n\n"
        f"We will investigate and provide you with an update within "
        f"{sla_hours} business hours. Your funds are safe and secure.\n\n"
        f"Case Reference: {state.get('exception_id', 'N/A')}\n\n"
        f"For assistance, please contact us at 1800-XXX-XXXX.\n\n"
        f"Sincerely,\nFirst National Bank — Operations Support"
    )

    # Audit entry
    state["audit_trail"].append(
        _make_audit(
            action="manual_review_queued",
            evidence=state.get("evidence_gathered", []),
            decision=f"QUEUED:{queue}:{priority}",
            justification=(
                f"Exception {state['exception_id']} queued for manual review. "
                f"Priority={priority}, Queue={queue}, SLA={sla_hours}h. "
                f"Failure type: {failure_type}. "
                f"Reason: automated resolution not safe or retries exhausted."
            ),
        )
    )

    logger.info(
        f"[ManualReviewAgent] Done. Queue={queue}, Priority={priority}, "
        f"SLA={sla_hours}h, Status={state['status']}"
    )
    return state
