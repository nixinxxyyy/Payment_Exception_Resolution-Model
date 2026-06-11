"""
Auto-Resolve Agent — Executes automated resolution actions.

Handles: AUTO_RETRY, AUTO_CORRECT, DUPLICATE_SUPPRESS, HOLD_FOR_WINDOW

Performs the actual downstream action stub (in production would call
the payment gateway / core banking system API).
Schedules deferred retries and records idempotency keys.
"""

import logging
from datetime import datetime, timedelta

from src.models.state import (
    PaymentExceptionState,
    ResolutionAction,
    ExceptionStatus,
)
from src.config import config

logger = logging.getLogger(__name__)


def _make_audit(action: str, evidence: list, decision: str, justification: str) -> dict:
    return {
        "agent": "auto_resolve_agent",
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "evidence_used": evidence,
        "decision": decision,
        "justification": justification,
    }


def _execute_retry(state: PaymentExceptionState) -> dict:
    """
    Stub: submit retry to payment gateway.
    In production: POST /payments/retry {"payment_id": ..., "idempotency_key": ...}
    """
    idempotency_key = f"{state['exception_id']}-retry-{state['retry_count'] + 1}"
    logger.info(f"  [stub] Submitting retry with key: {idempotency_key}")
    return {
        "outcome": "SUBMITTED",
        "idempotency_key": idempotency_key,
        "submitted_at": datetime.utcnow().isoformat(),
        "gateway_response": "retry_queued",
        "note": "Retry submitted to payment gateway (stubbed).",
    }


def _execute_correction(state: PaymentExceptionState) -> dict:
    """
    Stub: apply minor beneficiary correction and resubmit.
    In production: PATCH /payments/{id}/beneficiary then POST /payments/retry
    """
    ben  = state.get("beneficiary_details", {})
    issues = state.get("metadata", {}).get("beneficiary_issues", [])
    correction_note = f"Corrected fields: {issues}" if issues else "Minor format correction applied."
    logger.info(f"  [stub] Applying correction: {correction_note}")
    return {
        "outcome": "CORRECTED_AND_RESUBMITTED",
        "correction_applied": correction_note,
        "corrected_beneficiary": ben,
        "submitted_at": datetime.utcnow().isoformat(),
        "note": "Beneficiary details corrected and payment resubmitted (stubbed).",
    }


def _execute_duplicate_suppress(state: PaymentExceptionState) -> dict:
    """
    Stub: mark the duplicate payment as suppressed / cancelled.
    In production: POST /payments/cancel {"payment_id": ..., "reason": "duplicate"}
    """
    logger.info(f"  [stub] Suppressing duplicate payment {state['payment_id']}")
    return {
        "outcome": "SUPPRESSED",
        "original_payment_id": state.get("duplicate_of"),
        "suppressed_at": datetime.utcnow().isoformat(),
        "note": f"Duplicate of {state.get('duplicate_of')} safely suppressed. No double debit.",
    }


def _schedule_window_retry(state: PaymentExceptionState) -> tuple[dict, str]:
    """
    Schedule the payment for the next processing window.
    Returns (execution_result, scheduled_retry_at ISO string).
    """
    rail   = state.get("payment_rail", "NEFT")
    cutoff = config.RAIL_CUTOFFS.get(rail.upper(), "18:30")
    # Schedule for next business day at the rail's open time (9:00 AM)
    next_window = (datetime.utcnow() + timedelta(days=1)).replace(
        hour=9, minute=0, second=0, microsecond=0
    )
    next_window_iso = next_window.isoformat()
    logger.info(f"  [stub] Scheduling retry at {next_window_iso} for rail {rail}")
    result = {
        "outcome": "DEFERRED",
        "rail": rail,
        "cutoff_time": cutoff,
        "scheduled_retry_at": next_window_iso,
        "note": f"Payment queued for next {rail} processing window on {next_window.date()}.",
    }
    return result, next_window_iso


def auto_resolve_agent(state: PaymentExceptionState) -> PaymentExceptionState:
    """
    Execute an automated resolution action.

    Handles AUTO_RETRY, AUTO_CORRECT, DUPLICATE_SUPPRESS, HOLD_FOR_WINDOW.
    """
    action = state.get("resolution_action", "")
    logger.info(f"[AutoResolveAgent] Executing '{action}' for {state['exception_id']}")

    result: dict = {}
    new_status   = ExceptionStatus.RESOLVED.value
    outcome_note = ""

    if action == ResolutionAction.AUTO_RETRY.value:
        result = _execute_retry(state)
        new_status   = ExceptionStatus.EXECUTING.value
        outcome_note = "Payment retry submitted automatically."
        # Increment retry count
        state["retry_count"] = state.get("retry_count", 0) + 1

    elif action == ResolutionAction.AUTO_CORRECT.value:
        result = _execute_correction(state)
        new_status   = ExceptionStatus.EXECUTING.value
        outcome_note = "Beneficiary details corrected and payment resubmitted."
        state["retry_count"] = state.get("retry_count", 0) + 1

    elif action == ResolutionAction.DUPLICATE_SUPPRESS.value:
        result = _execute_duplicate_suppress(state)
        new_status   = ExceptionStatus.CANCELLED.value
        outcome_note = "Duplicate payment suppressed — no double debit occurred."

    elif action == ResolutionAction.HOLD_FOR_WINDOW.value:
        result, scheduled_at = _schedule_window_retry(state)
        state["scheduled_retry_at"] = scheduled_at
        new_status   = ExceptionStatus.HELD.value
        outcome_note = f"Payment deferred to next processing window: {scheduled_at}"

    else:
        result = {"outcome": "SKIPPED", "note": f"Action {action} not handled by auto_resolve_agent."}
        logger.warning(f"  Unexpected action {action} received by auto_resolve_agent.")

    state["execution_result"] = result
    state["status"]           = new_status

    # Audit entry
    state["audit_trail"].append(
        _make_audit(
            action=f"auto_execute:{action}",
            evidence=state.get("evidence_gathered", []),
            decision=result.get("outcome", "UNKNOWN"),
            justification=(
                f"{outcome_note} Exception {state['exception_id']}: "
                f"payment {state['payment_id']} — {result.get('note', '')}"
            ),
        )
    )

    logger.info(
        f"[AutoResolveAgent] Done. Status={new_status}, outcome={result.get('outcome')}"
    )
    return state
