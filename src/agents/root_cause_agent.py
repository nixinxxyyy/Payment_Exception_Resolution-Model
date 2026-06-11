"""
Root Cause Analysis Agent — Uses GPT-4o to diagnose the failure type.

Receives all evidence from the Investigation agent and uses the LLM to:
  1. Determine the most likely FailureType
  2. Produce a human-readable root cause summary
  3. Assess whether automated correction is safe
"""

import logging
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.models.state import PaymentExceptionState, FailureType, ExceptionStatus
from src.config import config

logger = logging.getLogger(__name__)


def _make_audit(action: str, evidence: list, decision: str, justification: str) -> dict:
    return {
        "agent": "root_cause_agent",
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "evidence_used": evidence,
        "decision": decision,
        "justification": justification,
    }


def _map_failure_code_to_type(failure_code: str) -> str | None:
    """Fast-path: if the failure code directly maps to a failure type, use it."""
    return config.FAILURE_CODE_MAP.get(failure_code.upper())


SYSTEM_PROMPT = """You are a senior payment operations specialist at a bank.
Your job is to diagnose the root cause of a failed payment transaction.

Based on the evidence provided, determine:
1. The most likely FAILURE_TYPE (pick exactly one from the list below)
2. A concise root cause summary (2-3 sentences, professional banking language)
3. Whether automated correction is safe (true/false)

VALID FAILURE TYPES:
- INCORRECT_BENEFICIARY    : Wrong account number, IFSC code, UPI ID, IBAN, or BIC
- INSUFFICIENT_FUNDS       : Available balance too low to cover the debit
- DUPLICATE_PAYMENT        : Same transaction submitted more than once
- COMPLIANCE_HOLD          : AML, sanctions, or regulatory block
- NETWORK_RAIL_FAILURE     : Payment rail or clearing network outage/degradation
- CUTOFF_TIME_MISS         : Submitted after the rail's daily cut-off window
- UNCERTAIN_RETRY_STATUS   : Prior retry exists with unknown/pending outcome

SAFE TO AUTO-CORRECT rules:
- INCORRECT_BENEFICIARY   → safe ONLY if the correction is minor format fix (not account change)
- INSUFFICIENT_FUNDS      → NEVER auto-correct (requires client action)
- DUPLICATE_PAYMENT       → safe to suppress if original succeeded
- COMPLIANCE_HOLD         → NEVER auto-correct
- NETWORK_RAIL_FAILURE    → safe to retry if network is now UP
- CUTOFF_TIME_MISS        → safe to defer (requeue for next window)
- UNCERTAIN_RETRY_STATUS  → NEVER auto-correct (requires investigation first)

Respond in this EXACT format (JSON only, no markdown):
{{
  "failure_type": "FAILURE_TYPE_VALUE",
  "root_cause_summary": "...",
  "is_safe_to_automate": true_or_false,
  "confidence": 0.0_to_1.0
}}"""

USER_PROMPT = """Payment Exception Evidence:

Exception ID: {exception_id}
Payment ID: {payment_id}
Rail: {payment_rail}
Payment Type: {payment_type}
Amount: {currency} {amount}
Failure Code: {failure_code}
Failure Message: {failure_message}

Balance Check:
  Available: {balance_available}
  Required: {balance_required}
  Sufficient: {balance_sufficient}

Beneficiary Valid: {beneficiary_valid}
Beneficiary Issues: {beneficiary_issues}

Duplicate Of: {duplicate_of}
Within Cut-off: {is_within_cutoff}

Network Status: {network_status}
Compliance Flags: {compliance_flags}

Prior Retry Records: {prior_retry_count}

Diagnose the root cause:"""


def root_cause_agent(state: PaymentExceptionState) -> PaymentExceptionState:
    """
    Diagnose the root cause of the payment exception using LLM reasoning.

    Mutates:
        - failure_type
        - root_cause_summary
        - is_safe_to_automate
        - decision_confidence
    """
    logger.info(f"[RootCauseAgent] Analysing {state['exception_id']}")

    # ------------------------------------------------------------------
    # Fast-path: use failure_code mapping if available
    # ------------------------------------------------------------------
    fast_mapped = _map_failure_code_to_type(state.get("failure_code", ""))
    if fast_mapped:
        logger.info(f"  Fast-path mapping: {state['failure_code']} → {fast_mapped}")

    # ------------------------------------------------------------------
    # Prepare evidence summary for LLM
    # ------------------------------------------------------------------
    balance = state.get("balance_check") or {}
    net     = state.get("network_status") or {}
    ben_issues = state.get("metadata", {}).get("beneficiary_issues", [])

    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        temperature=0.1,   # Low: deterministic diagnosis
        api_key=config.OPENAI_API_KEY,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user",   USER_PROMPT),
    ])

    chain = prompt | llm

    try:
        response = chain.invoke({
            "exception_id":       state["exception_id"],
            "payment_id":         state["payment_id"],
            "payment_rail":       state["payment_rail"],
            "payment_type":       state["payment_type"],
            "currency":           state["currency"],
            "amount":             state["amount"],
            "failure_code":       state["failure_code"],
            "failure_message":    state.get("failure_message", "N/A"),
            "balance_available":  balance.get("available", "N/A"),
            "balance_required":   balance.get("required", state["amount"]),
            "balance_sufficient": balance.get("sufficient", "unknown"),
            "beneficiary_valid":  state.get("beneficiary_valid", True),
            "beneficiary_issues": ben_issues or "none",
            "duplicate_of":       state.get("duplicate_of") or "none",
            "is_within_cutoff":   state.get("is_within_cutoff", True),
            "network_status":     net.get("status", "UNKNOWN"),
            "compliance_flags":   state.get("compliance_flags") or "none",
            "prior_retry_count":  len(state.get("prior_retry_records") or []),
        })

        import json
        raw = response.content.strip()
        # Strip markdown code fences if model wraps in them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        parsed = json.loads(raw)
        failure_type  = parsed.get("failure_type", "UNKNOWN").upper()
        root_cause    = parsed.get("root_cause_summary", "Unable to determine root cause.")
        is_safe       = bool(parsed.get("is_safe_to_automate", False))
        confidence    = float(parsed.get("confidence", 0.5))

        # Validate the failure type
        valid_types = [ft.value for ft in FailureType]
        if failure_type not in valid_types:
            failure_type = fast_mapped or FailureType.UNKNOWN.value

    except Exception as exc:
        logger.error(f"  LLM root cause analysis failed: {exc}", exc_info=True)
        failure_type = fast_mapped or FailureType.UNKNOWN.value
        root_cause   = (
            f"Automated diagnosis failed. Failure code {state['failure_code']} "
            "suggests a potential issue requiring manual investigation."
        )
        is_safe    = False
        confidence = 0.2

    # ------------------------------------------------------------------
    # Override safety for high-risk failure types
    # ------------------------------------------------------------------
    if failure_type in (
        FailureType.COMPLIANCE_HOLD.value,
        FailureType.UNCERTAIN_RETRY_STATUS.value,
        FailureType.INSUFFICIENT_FUNDS.value,
    ):
        is_safe = False

    # Compliance flags always force unsafe
    if state.get("compliance_flags"):
        is_safe = False

    # ------------------------------------------------------------------
    # Update state
    # ------------------------------------------------------------------
    state["failure_type"]       = failure_type
    state["root_cause_summary"] = root_cause
    state["is_safe_to_automate"] = is_safe
    state["decision_confidence"] = confidence

    # ------------------------------------------------------------------
    # Audit entry
    # ------------------------------------------------------------------
    state["audit_trail"].append(
        _make_audit(
            action="root_cause_diagnosed",
            evidence=state.get("evidence_gathered", []),
            decision=failure_type,
            justification=(
                f"Diagnosed as {failure_type} with {confidence:.0%} confidence. "
                f"Safe to automate: {is_safe}. Summary: {root_cause}"
            ),
        )
    )

    logger.info(
        f"[RootCauseAgent] Done. failure_type={failure_type}, "
        f"confidence={confidence:.2f}, safe={is_safe}"
    )
    return state
