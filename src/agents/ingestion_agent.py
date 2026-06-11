"""
Ingestion Agent — First agent in the workflow.

Responsibilities:
  1. Validate and normalise all input fields on the PaymentExceptionState.
  2. Detect duplicate exception events (same payment_id already in DB).
  3. Perform deduplication: if this is a replay of an existing case, mark it.
  4. Enrich metadata (client name lookup stub, account type, etc.).
  5. Emit the first AuditEntry.
"""

import logging
import json
from datetime import datetime

from src.models.state import PaymentExceptionState, ExceptionStatus
from src.config import config

logger = logging.getLogger(__name__)


def _make_audit(action: str, evidence: list, decision: str, justification: str) -> dict:
    return {
        "agent": "ingestion_agent",
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "evidence_used": evidence,
        "decision": decision,
        "justification": justification,
    }


def ingestion_agent(state: PaymentExceptionState) -> PaymentExceptionState:
    """
    Validate, normalise and deduplicate the incoming payment exception.

    Mutates:
        - status → INGESTED (or marks is_duplicate_event = True)
        - beneficiary_details → normalised keys
        - failure_code → upper-cased
        - audit_trail → first entry appended
        - metadata → enriched with bank-specific context
    """
    logger.info(f"[IngestionAgent] Processing exception: {state['exception_id']}")

    issues: list[str] = []
    evidence: list[str] = []

    # ---------------------------------------------------------------
    # 1. Normalise core fields
    # ---------------------------------------------------------------
    state["failure_code"] = (state.get("failure_code") or "UNKNOWN").upper().strip()
    state["currency"]     = (state.get("currency") or "INR").upper().strip()
    state["payment_rail"] = (state.get("payment_rail") or "INTERNAL").upper().strip()
    state["payment_type"] = (state.get("payment_type") or "domestic_transfer").lower().strip()
    state["triggered_by"] = state.get("triggered_by") or "system_event"
    evidence.append("input_fields_normalised")

    # ---------------------------------------------------------------
    # 2. Validate required fields
    # ---------------------------------------------------------------
    required = ["payment_id", "client_id", "account_id", "amount", "currency"]
    for field in required:
        val = state.get(field)
        if val is None or val == "" or val == 0.0:
            issues.append(f"missing_or_empty:{field}")

    if issues:
        logger.warning(f"[IngestionAgent] Validation issues: {issues}")
        state["metadata"]["validation_issues"] = issues
    evidence.append("required_fields_validated")

    # ---------------------------------------------------------------
    # 3. Normalise beneficiary details
    # ---------------------------------------------------------------
    ben = state.get("beneficiary_details") or {}
    if isinstance(ben, str):
        try:
            ben = json.loads(ben)
        except json.JSONDecodeError:
            ben = {}

    # Normalise keys to lowercase
    ben = {k.lower(): v for k, v in ben.items()}
    state["beneficiary_details"] = ben
    evidence.append("beneficiary_details_normalised")

    # ---------------------------------------------------------------
    # 4. Detect duplicate exception events (same exception_id already seen)
    #    In production this would query the DB; here we rely on the state
    #    field set by the API layer.
    # ---------------------------------------------------------------
    if state.get("is_duplicate_event"):
        logger.info(
            f"[IngestionAgent] Duplicate event detected for exception {state['exception_id']}. "
            f"Original: {state.get('replay_of')}"
        )
        state["metadata"]["duplicate_suppressed"] = True
        decision = "DUPLICATE_SUPPRESSED"
        justification = (
            f"Exception event is a replay of {state.get('replay_of')}. "
            "Idempotency check passed — no new processing triggered."
        )
    else:
        state["status"] = ExceptionStatus.INGESTED.value
        decision = "INGESTED"
        justification = (
            f"Payment exception {state['exception_id']} ingested successfully. "
            f"Payment {state['payment_id']} on {state['payment_rail']} rail "
            f"for {state['currency']} {state['amount']:.2f}. "
            f"Failure code: {state['failure_code']}."
        )

    # ---------------------------------------------------------------
    # 5. Enrich metadata
    # ---------------------------------------------------------------
    state["metadata"].update({
        "ingested_at": datetime.utcnow().isoformat(),
        "payment_rail": state["payment_rail"],
        "amount_band": (
            "high_value" if state["amount"] >= config.HIGH_VALUE_THRESHOLD
            else "standard"
        ),
    })
    evidence.append("metadata_enriched")

    # ---------------------------------------------------------------
    # 6. Initialise empty investigation fields if not set
    # ---------------------------------------------------------------
    if not state.get("prior_retry_records"):
        state["prior_retry_records"] = []
    if not state.get("compliance_flags"):
        state["compliance_flags"] = []
    if not state.get("evidence_gathered"):
        state["evidence_gathered"] = []
    if state.get("retry_count") is None:
        state["retry_count"] = 0
    if state.get("max_retries_allowed") is None:
        state["max_retries_allowed"] = config.MAX_RETRY_ATTEMPTS

    # ---------------------------------------------------------------
    # 7. Append audit entry
    # ---------------------------------------------------------------
    state["audit_trail"].append(
        _make_audit(
            action="exception_ingested",
            evidence=evidence,
            decision=decision,
            justification=justification,
        )
    )

    logger.info(
        f"[IngestionAgent] Done. Status={state['status']}, "
        f"Issues={issues or 'none'}"
    )
    return state
