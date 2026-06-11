"""
State definitions for the Payment Exception Resolution multi-agent system.

The PaymentExceptionState flows through all agents in the LangGraph workflow,
carrying all evidence, decisions, and audit trail for a single payment exception.
"""

from enum import Enum
from typing import TypedDict, List, Optional, Dict, Any


class FailureType(str, Enum):
    """Categorised failure types for payment exceptions."""
    INCORRECT_BENEFICIARY   = "INCORRECT_BENEFICIARY"    # Wrong account/UPI/IFSC
    INSUFFICIENT_FUNDS      = "INSUFFICIENT_FUNDS"        # Balance too low at debit
    DUPLICATE_PAYMENT       = "DUPLICATE_PAYMENT"         # Same payment sent twice
    COMPLIANCE_HOLD         = "COMPLIANCE_HOLD"           # AML / sanctions block
    NETWORK_RAIL_FAILURE    = "NETWORK_RAIL_FAILURE"      # Clearing network outage
    CUTOFF_TIME_MISS        = "CUTOFF_TIME_MISS"          # Submitted after rail window
    UNCERTAIN_RETRY_STATUS  = "UNCERTAIN_RETRY_STATUS"    # Prior retry in unknown state
    UNKNOWN                 = "UNKNOWN"                   # Not yet diagnosed


class ResolutionAction(str, Enum):
    """Possible resolution actions the decision agent can choose."""
    AUTO_RETRY          = "AUTO_RETRY"          # Safe to retry automatically
    AUTO_CORRECT        = "AUTO_CORRECT"        # Fix beneficiary details and retry
    CLIENT_OUTREACH     = "CLIENT_OUTREACH"     # Need client input before proceeding
    COMPLIANCE_REVIEW   = "COMPLIANCE_REVIEW"   # Route to compliance / AML team
    HOLD_FOR_WINDOW     = "HOLD_FOR_WINDOW"     # Wait for next processing window
    CANCEL              = "CANCEL"              # Cancel and refund
    MANUAL_REVIEW       = "MANUAL_REVIEW"       # Ops team must investigate
    DUPLICATE_SUPPRESS  = "DUPLICATE_SUPPRESS"  # Suppress the duplicate safely


class ExceptionStatus(str, Enum):
    """Lifecycle status of a payment exception case."""
    INGESTED        = "INGESTED"        # Received, not yet investigated
    INVESTIGATING   = "INVESTIGATING"   # Root cause analysis underway
    DECIDED         = "DECIDED"         # Resolution action chosen
    EXECUTING       = "EXECUTING"       # Downstream action being applied
    AWAITING_INPUT  = "AWAITING_INPUT"  # Waiting for client / ops response
    RESOLVED        = "RESOLVED"        # Successfully remediated
    ESCALATED       = "ESCALATED"       # Routed to human / compliance team
    HELD            = "HELD"            # Deferred to next processing window
    CANCELLED       = "CANCELLED"       # Payment cancelled


class PaymentRail(str, Enum):
    """Supported payment rails."""
    NEFT  = "NEFT"
    RTGS  = "RTGS"
    IMPS  = "IMPS"
    SWIFT = "SWIFT"
    UPI   = "UPI"
    INTERNAL = "INTERNAL"


class RetryRecord(TypedDict):
    """Record of a single retry attempt."""
    attempt_number: int
    timestamp: str
    outcome: str        # SUCCESS | FAILED | PENDING | UNKNOWN
    error_code: Optional[str]
    error_message: Optional[str]


class AuditEntry(TypedDict):
    """Immutable audit log entry produced by each agent."""
    agent: str
    timestamp: str
    action: str
    evidence_used: List[str]
    decision: Optional[str]
    justification: str


class PaymentExceptionState(TypedDict):
    """
    Master state object that flows through the entire multi-agent workflow.

    Inputs (from ingestion / API):
        exception_id        : Unique exception case ID (EXC-xxxxxxxx)
        payment_id          : Original payment transaction ID
        client_id           : Client/customer ID
        account_id          : Source account ID
        payment_rail        : Rail used (NEFT/RTGS/IMPS/SWIFT/UPI/INTERNAL)
        payment_type        : domestic_transfer | wire | book_transfer | disbursement
        amount              : Transaction amount (float)
        currency            : ISO 4217 currency code
        beneficiary_details : Dict with account_no, ifsc/iban/routing, name, upi_id
        failure_code        : Raw error code from payment system
        failure_message     : Human-readable error from payment system
        submitted_at        : ISO 8601 timestamp of original submission
        triggered_by        : "system_event" | "manual" | "replay"

    Investigation outputs:
        failure_type        : Diagnosed FailureType enum value
        root_cause_summary  : LLM-generated root cause narrative
        prior_retry_records : List of prior retry attempts
        balance_check       : Dict {available: float, required: float, sufficient: bool}
        beneficiary_valid   : Whether beneficiary details passed validation
        compliance_flags    : List of compliance/AML alert strings
        network_status      : Dict {rail: str, status: "UP"|"DOWN"|"DEGRADED"}
        duplicate_of        : payment_id of the original if this is a duplicate
        is_within_cutoff    : Whether still within rail processing window
        evidence_gathered   : List of evidence keys collected

    Decision outputs:
        resolution_action   : Chosen ResolutionAction
        decision_confidence : Float 0-1 confidence in the decision
        decision_rationale  : Human-readable justification
        is_safe_to_automate : Whether automated action is safe (idempotency check)
        retry_count         : Number of retries already attempted
        max_retries_allowed : Maximum retries permitted for this exception

    Execution outputs:
        status              : Current ExceptionStatus
        execution_result    : Dict with outcome of the resolution action
        client_message      : Message sent to client (if CLIENT_OUTREACH)
        escalation_queue    : Target queue for escalated cases
        scheduled_retry_at  : ISO 8601 timestamp for deferred retry

    Audit & Observability:
        audit_trail         : List of AuditEntry records (append-only)
        is_duplicate_event  : Whether this exception event is a replay/duplicate trigger
        replay_of           : exception_id this is a replay of (if applicable)
        operator_override   : Dict if ops manually overrode a decision
        metadata            : Extensible key-value store
    """
    # --- Inputs ---
    exception_id: str
    payment_id: str
    client_id: str
    account_id: str
    payment_rail: str
    payment_type: str
    amount: float
    currency: str
    beneficiary_details: Dict[str, Any]
    failure_code: str
    failure_message: str
    submitted_at: str
    triggered_by: str

    # --- Investigation ---
    failure_type: str
    root_cause_summary: str
    prior_retry_records: List[RetryRecord]
    balance_check: Dict[str, Any]
    beneficiary_valid: bool
    compliance_flags: List[str]
    network_status: Dict[str, Any]
    duplicate_of: Optional[str]
    is_within_cutoff: bool
    evidence_gathered: List[str]

    # --- Decision ---
    resolution_action: str
    decision_confidence: float
    decision_rationale: str
    is_safe_to_automate: bool
    retry_count: int
    max_retries_allowed: int

    # --- Execution ---
    status: str
    execution_result: Dict[str, Any]
    client_message: str
    escalation_queue: str
    scheduled_retry_at: Optional[str]

    # --- Audit ---
    audit_trail: List[AuditEntry]
    is_duplicate_event: bool
    replay_of: Optional[str]
    operator_override: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]
