"""
Investigation Agent — Gathers all evidence needed for root cause analysis.

Simulates the real-world data checks an operations team would perform:
  1. Balance check against the account ledger
  2. Beneficiary details validation (account/IFSC/UPI format checks)
  3. Duplicate payment detection (look for same payment_id in prior window)
  4. Network / payment-rail status check
  5. Compliance / AML flag check
  6. Cut-off time check for the payment rail
  7. Prior retry history inspection
"""

import logging
import re
from datetime import datetime, time

from src.models.state import PaymentExceptionState, ExceptionStatus
from src.config import config

logger = logging.getLogger(__name__)


def _make_audit(action: str, evidence: list, decision: str, justification: str) -> dict:
    return {
        "agent": "investigation_agent",
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "evidence_used": evidence,
        "decision": decision,
        "justification": justification,
    }


# ---------------------------------------------------------------------------
# Stub helpers — in production these call real internal microservices / APIs
# ---------------------------------------------------------------------------

def _check_balance(account_id: str, amount: float, currency: str) -> dict:
    """
    Stub: query account ledger microservice.
    Returns synthetic balance data for demonstration.
    """
    # In production: POST /internal/ledger/balance {"account_id": ..., "currency": ...}
    # Simulate: if amount > 50,000 treat as insufficient for demo
    available = 45000.00 if amount > 50000 else amount * 1.5
    return {
        "account_id": account_id,
        "available": available,
        "required": amount,
        "currency": currency,
        "sufficient": available >= amount,
        "source": "ledger_stub",
    }


def _validate_beneficiary(ben: dict, rail: str) -> tuple[bool, list[str]]:
    """
    Validate beneficiary details based on the payment rail.
    Returns (is_valid, list_of_issues).
    """
    issues = []

    if rail in ("NEFT", "RTGS", "IMPS"):
        account_no = str(ben.get("account_no", ""))
        ifsc = str(ben.get("ifsc", ""))
        if not account_no or len(account_no) < 9:
            issues.append("invalid_account_number")
        if not re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', ifsc):
            issues.append("invalid_ifsc_format")

    elif rail == "UPI":
        upi_id = str(ben.get("upi_id", ""))
        if not re.match(r'^[\w.\-]{2,256}@[a-zA-Z]{2,64}$', upi_id):
            issues.append("invalid_upi_id_format")

    elif rail == "SWIFT":
        iban = str(ben.get("iban", ""))
        bic  = str(ben.get("bic", ""))
        if len(iban) < 15:
            issues.append("invalid_iban")
        if not re.match(r'^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$', bic):
            issues.append("invalid_bic_swift_code")

    name = str(ben.get("name", ""))
    if not name or len(name) < 2:
        issues.append("missing_beneficiary_name")

    return len(issues) == 0, issues


def _check_network_status(rail: str) -> dict:
    """
    Stub: query network status microservice.
    In production calls the real NPCI / SWIFT status API.
    """
    # Simulate network status — for demo all rails are UP unless failure_code indicates outage
    return {
        "rail": rail,
        "status": "UP",           # UP | DOWN | DEGRADED
        "latency_ms": 45,
        "last_checked": datetime.utcnow().isoformat(),
        "source": "network_status_stub",
    }


def _check_compliance_flags(
    client_id: str, amount: float, currency: str, failure_code: str
) -> list:
    """
    Stub: query AML / sanctions screening service.
    In production calls internal compliance API or a vendor like ComplyAdvantage.
    """
    flags = []
    if failure_code in ("AML_HOLD", "SANCTIONS_HOLD", "COMPLIANCE_BLOCK"):
        flags.append(f"compliance_hold_from_failure_code:{failure_code}")
    if amount >= config.AML_AMOUNT_THRESHOLD:
        flags.append(f"high_value_aml_threshold_exceeded:{amount}{currency}")
    return flags


def _is_within_cutoff(rail: str, submitted_at_iso: str) -> bool:
    """Check if the payment was submitted before the rail's daily cut-off."""
    try:
        cutoff_str = config.RAIL_CUTOFFS.get(rail.upper(), "23:59")
        h, m = map(int, cutoff_str.split(":"))
        cutoff = time(h, m, 0)

        submitted = datetime.fromisoformat(submitted_at_iso)
        submitted_time = submitted.time()
        return submitted_time <= cutoff
    except Exception:
        return True   # Conservative: assume within window if parse fails


def _get_prior_retries(payment_id: str, exception_id: str) -> list:
    """
    Stub: query retry_attempts table.
    In production: SELECT * FROM retry_attempts WHERE exception_id = :id
    """
    # Return empty for new exceptions; would be populated from DB in production
    return []


def _is_duplicate(payment_id: str, exception_id: str, window_seconds: int) -> str | None:
    """
    Stub: check if payment_id appears in another exception within the window.
    Returns the duplicate exception_id or None.
    """
    # In production: query DB for payment_id != exception_id within window
    return None


# ---------------------------------------------------------------------------
# Main agent function
# ---------------------------------------------------------------------------

def investigation_agent(state: PaymentExceptionState) -> PaymentExceptionState:
    """
    Gather all evidence required to diagnose the payment exception root cause.

    Updates state fields: balance_check, beneficiary_valid, compliance_flags,
    network_status, duplicate_of, is_within_cutoff, prior_retry_records,
    evidence_gathered, status.
    """
    logger.info(f"[InvestigationAgent] Investigating {state['exception_id']}")
    state["status"] = ExceptionStatus.INVESTIGATING.value
    evidence_gathered: list[str] = []

    # ------------------------------------------------------------------
    # 1. Balance check
    # ------------------------------------------------------------------
    balance = _check_balance(
        state["account_id"], state["amount"], state["currency"]
    )
    state["balance_check"] = balance
    evidence_gathered.append("balance_check")
    logger.debug(f"  Balance: {balance}")

    # ------------------------------------------------------------------
    # 2. Beneficiary validation
    # ------------------------------------------------------------------
    is_valid, ben_issues = _validate_beneficiary(
        state["beneficiary_details"], state["payment_rail"]
    )
    state["beneficiary_valid"] = is_valid
    if ben_issues:
        state["metadata"]["beneficiary_issues"] = ben_issues
    evidence_gathered.append("beneficiary_validation")
    logger.debug(f"  Beneficiary valid={is_valid}, issues={ben_issues}")

    # ------------------------------------------------------------------
    # 3. Duplicate detection
    # ------------------------------------------------------------------
    dup_of = _is_duplicate(
        state["payment_id"],
        state["exception_id"],
        config.DUPLICATE_WINDOW_SECONDS,
    )
    state["duplicate_of"] = dup_of
    evidence_gathered.append("duplicate_check")
    logger.debug(f"  Duplicate of: {dup_of}")

    # ------------------------------------------------------------------
    # 4. Network / rail status
    # ------------------------------------------------------------------
    net_status = _check_network_status(state["payment_rail"])
    # If failure_code explicitly says rail/network failed, mark as DOWN
    if state["failure_code"] in ("NETWORK_ERROR", "CLEARING_TIMEOUT", "RAIL_UNAVAILABLE"):
        net_status["status"] = "DOWN"
    state["network_status"] = net_status
    evidence_gathered.append("network_status_check")
    logger.debug(f"  Network: {net_status}")

    # ------------------------------------------------------------------
    # 5. Compliance / AML flags
    # ------------------------------------------------------------------
    flags = _check_compliance_flags(
        state["client_id"],
        state["amount"],
        state["currency"],
        state["failure_code"],
    )
    state["compliance_flags"] = flags
    evidence_gathered.append("compliance_aml_check")
    logger.debug(f"  Compliance flags: {flags}")

    # ------------------------------------------------------------------
    # 6. Cut-off time check
    # ------------------------------------------------------------------
    within_cutoff = _is_within_cutoff(state["payment_rail"], state["submitted_at"])
    # Failure code override
    if state["failure_code"] == "CUTOFF_EXCEEDED":
        within_cutoff = False
    state["is_within_cutoff"] = within_cutoff
    evidence_gathered.append("cutoff_time_check")
    logger.debug(f"  Within cutoff: {within_cutoff}")

    # ------------------------------------------------------------------
    # 7. Prior retry history
    # ------------------------------------------------------------------
    prior = _get_prior_retries(state["payment_id"], state["exception_id"])
    state["prior_retry_records"] = prior
    state["retry_count"] = len(prior)
    evidence_gathered.append("prior_retry_history")
    logger.debug(f"  Prior retries: {len(prior)}")

    # ------------------------------------------------------------------
    # 8. Persist evidence list
    # ------------------------------------------------------------------
    state["evidence_gathered"] = evidence_gathered

    # ------------------------------------------------------------------
    # 9. Audit entry
    # ------------------------------------------------------------------
    summary_parts = []
    if not balance["sufficient"]:
        summary_parts.append("insufficient_funds")
    if not is_valid:
        summary_parts.append(f"beneficiary_issues:{ben_issues}")
    if dup_of:
        summary_parts.append(f"duplicate_of:{dup_of}")
    if net_status["status"] != "UP":
        summary_parts.append(f"network_{net_status['status'].lower()}")
    if flags:
        summary_parts.append(f"compliance_flags:{flags}")
    if not within_cutoff:
        summary_parts.append("cutoff_missed")

    justification = (
        f"Evidence gathered for {state['exception_id']}: "
        + (", ".join(summary_parts) if summary_parts else "no anomalies detected")
    )

    state["audit_trail"].append(
        _make_audit(
            action="evidence_gathered",
            evidence=evidence_gathered,
            decision=f"findings:{len(summary_parts)}",
            justification=justification,
        )
    )

    logger.info(
        f"[InvestigationAgent] Complete. Evidence items: {len(evidence_gathered)}, "
        f"Findings: {len(summary_parts)}"
    )
    return state
