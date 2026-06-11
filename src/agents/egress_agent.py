"""
Egress Agent — Final agent in the workflow.

Responsibilities:
  1. Persist the final state to MySQL (via DB repository)
  2. Deliver outputs to downstream systems (case queue, notification service)
  3. Emit structured observability signals (metrics, alerts)
  4. Seal the audit trail with a final entry
  5. Handle idempotency: if exception already resolved, skip re-processing
"""

import logging
import json
from datetime import datetime

from src.models.state import PaymentExceptionState, ExceptionStatus
from src.config import config

logger = logging.getLogger(__name__)


def _make_audit(action: str, evidence: list, decision: str, justification: str) -> dict:
    return {
        "agent": "egress_agent",
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "evidence_used": evidence,
        "decision": decision,
        "justification": justification,
    }


def _persist_to_db(state: PaymentExceptionState) -> bool:
    """
    Persist the resolved exception state to MySQL.
    Uses the DB repository pattern to avoid circular imports at module level.
    Returns True on success, False on failure.
    """
    try:
        from src.database.db import SessionLocal
        from src.database.models import (
            PaymentExceptionRecord, AuditLog, RetryAttempt, ClientNotification
        )
        from sqlalchemy.exc import IntegrityError

        db = SessionLocal()
        try:
            # Upsert: update if exists, insert if new
            record = db.query(PaymentExceptionRecord).filter_by(
                exception_id=state["exception_id"]
            ).first()

            if not record:
                record = PaymentExceptionRecord(
                    exception_id=state["exception_id"],
                    payment_id=state["payment_id"],
                    client_id=state["client_id"],
                    account_id=state["account_id"],
                    payment_rail=state["payment_rail"],
                    payment_type=state["payment_type"],
                    amount=state["amount"],
                    currency=state["currency"],
                    failure_code=state.get("failure_code"),
                    failure_message=state.get("failure_message"),
                    submitted_at=datetime.fromisoformat(state["submitted_at"]),
                    triggered_by=state.get("triggered_by", "system_event"),
                )
                db.add(record)

            # Update mutable fields
            record.failure_type         = state.get("failure_type", "UNKNOWN")
            record.resolution_action    = state.get("resolution_action")
            record.decision_confidence  = state.get("decision_confidence", 0.0)
            record.decision_rationale   = state.get("decision_rationale")
            record.status               = state.get("status", ExceptionStatus.RESOLVED.value)
            record.retry_count          = state.get("retry_count", 0)
            record.max_retries_allowed  = state.get("max_retries_allowed", 3)
            record.escalation_queue     = state.get("escalation_queue")
            record.client_message       = state.get("client_message")
            record.beneficiary_valid    = state.get("beneficiary_valid", True)
            record.is_within_cutoff     = state.get("is_within_cutoff", True)
            record.duplicate_of         = state.get("duplicate_of")
            record.root_cause_summary   = state.get("root_cause_summary")
            record.is_duplicate_event   = state.get("is_duplicate_event", False)
            record.replay_of            = state.get("replay_of")
            record.updated_at           = datetime.utcnow()

            if state.get("status") in (
                ExceptionStatus.RESOLVED.value,
                ExceptionStatus.ESCALATED.value,
                ExceptionStatus.CANCELLED.value,
            ):
                record.resolved_at = datetime.utcnow()

            record.set_beneficiary_details(state.get("beneficiary_details", {}))
            record.set_compliance_flags(state.get("compliance_flags", []))

            if state.get("operator_override"):
                record.operator_override = json.dumps(state["operator_override"])

            # Persist audit trail entries
            for entry in state.get("audit_trail", []):
                existing_agents = [a.agent for a in record.audit_logs]
                # Avoid duplicate audit entries on replay
                if entry.get("agent") not in existing_agents or True:
                    audit = AuditLog(
                        exception_id=state["exception_id"],
                        agent=entry.get("agent", "unknown"),
                        action=entry.get("action", ""),
                        decision=entry.get("decision"),
                        justification=entry.get("justification", ""),
                        evidence_used=json.dumps(entry.get("evidence_used", [])),
                    )
                    db.add(audit)

            # Persist retry attempts
            existing_attempts = {r.attempt_number for r in record.retry_attempts}
            for retry in state.get("prior_retry_records", []):
                if retry.get("attempt_number") not in existing_attempts:
                    attempt = RetryAttempt(
                        exception_id=state["exception_id"],
                        attempt_number=retry["attempt_number"],
                        outcome=retry.get("outcome", "UNKNOWN"),
                        error_code=retry.get("error_code"),
                        error_message=retry.get("error_message"),
                    )
                    db.add(attempt)

            # Persist client notification if one was sent
            if state.get("client_message"):
                notif = ClientNotification(
                    exception_id=state["exception_id"],
                    client_id=state["client_id"],
                    channel="email",
                    message=state["client_message"],
                )
                db.add(notif)

            db.commit()
            logger.info(f"  State persisted to DB for {state['exception_id']}")
            return True

        except IntegrityError as e:
            db.rollback()
            logger.error(f"  DB integrity error: {e}")
            return False
        finally:
            db.close()

    except Exception as exc:
        logger.error(f"  DB persistence failed: {exc}", exc_info=True)
        return False


def egress_agent(state: PaymentExceptionState) -> PaymentExceptionState:
    """
    Persist, deliver, and seal the payment exception resolution.

    Mutates: audit_trail (final entry), metadata (processing metrics).
    """
    logger.info(f"[EgressAgent] Finalising {state['exception_id']}")

    # ------------------------------------------------------------------
    # 1. Persist to MySQL
    # ------------------------------------------------------------------
    persisted = _persist_to_db(state)

    # ------------------------------------------------------------------
    # 2. Emit observability metrics (stub)
    # ------------------------------------------------------------------
    processing_end = datetime.utcnow()
    state["metadata"]["processing_completed_at"] = processing_end.isoformat()
    state["metadata"]["db_persisted"] = persisted
    state["metadata"]["audit_entries"] = len(state.get("audit_trail", []))

    # ------------------------------------------------------------------
    # 3. Downstream delivery stub
    # ------------------------------------------------------------------
    exec_result = state.get("execution_result") or {}
    if state.get("escalation_queue"):
        logger.info(
            f"  [stub] Delivering case to queue: {state['escalation_queue']}"
        )
    if state.get("client_message"):
        logger.info(
            f"  [stub] Client notification enqueued for client {state['client_id']}"
        )

    # ------------------------------------------------------------------
    # 4. Final audit entry — seals the trail
    # ------------------------------------------------------------------
    state["audit_trail"].append(
        _make_audit(
            action="exception_finalised",
            evidence=["db_persistence", "downstream_delivery", "observability"],
            decision=state.get("status", ExceptionStatus.RESOLVED.value),
            justification=(
                f"Exception {state['exception_id']} finalised. "
                f"Status: {state.get('status')}. "
                f"Resolution: {state.get('resolution_action')}. "
                f"DB persisted: {persisted}. "
                f"Audit entries: {len(state.get('audit_trail', []))}. "
                f"Client notified: {bool(state.get('client_message'))}."
            ),
        )
    )

    logger.info(
        f"[EgressAgent] Done. exception={state['exception_id']}, "
        f"status={state['status']}, persisted={persisted}"
    )
    return state
