"""
Compliance Escalation Agent — Routes flagged payments to the compliance queue.

Handles: COMPLIANCE_REVIEW

Responsibilities:
  1. Package evidence into a compliance case dossier
  2. Assign to the appropriate compliance sub-queue (AML, Sanctions, Ops)
  3. Generate a structured escalation summary for the compliance officer
  4. Lock the payment from any automated retry
  5. Notify operations of the escalation
"""

import logging
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.models.state import (
    PaymentExceptionState,
    FailureType,
    ExceptionStatus,
)
from src.config import config

logger = logging.getLogger(__name__)


def _make_audit(action: str, evidence: list, decision: str, justification: str) -> dict:
    return {
        "agent": "compliance_agent",
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "evidence_used": evidence,
        "decision": decision,
        "justification": justification,
    }


SYSTEM_PROMPT = """You are a compliance case officer at a bank.
Generate a structured compliance escalation summary for a flagged payment transaction.

The summary must include:
1. Case Overview (1-2 sentences)
2. Risk Indicators (bulleted list)
3. Required Compliance Action
4. Recommended SLA (in hours)
5. Regulatory reference if applicable (AML/CFT, FATF, OFAC, etc.)

Tone: Formal, precise, regulatory language.
Format: Plain text with clear section headings."""

USER_PROMPT = """Exception ID: {exception_id}
Payment ID: {payment_id}
Client ID: {client_id}
Amount: {currency} {amount}
Rail: {payment_rail}
Failure Type: {failure_type}
Compliance Flags: {compliance_flags}
Root Cause: {root_cause}
Beneficiary Details: {beneficiary_summary}

Generate the compliance escalation summary:"""


# Sub-queue routing based on flag type
def _determine_compliance_queue(
    failure_type: str, flags: list, amount: float
) -> str:
    if any("sanctions" in f.lower() for f in flags):
        return "SANCTIONS_REVIEW_QUEUE"
    if any("aml" in f.lower() for f in flags):
        return "AML_REVIEW_QUEUE"
    if failure_type == FailureType.COMPLIANCE_HOLD.value:
        return "COMPLIANCE_HOLD_QUEUE"
    if amount >= config.HIGH_VALUE_THRESHOLD:
        return "HIGH_VALUE_REVIEW_QUEUE"
    return "GENERAL_COMPLIANCE_QUEUE"


def compliance_agent(state: PaymentExceptionState) -> PaymentExceptionState:
    """
    Escalate the payment exception to the compliance team.

    Mutates: escalation_queue, execution_result, status → ESCALATED
    """
    logger.info(f"[ComplianceAgent] Escalating {state['exception_id']}")

    failure_type  = state.get("failure_type", FailureType.COMPLIANCE_HOLD.value)
    flags         = state.get("compliance_flags") or []
    amount        = state.get("amount", 0)
    ben           = state.get("beneficiary_details") or {}
    ben_summary   = (
        f"Account: {ben.get('account_no', 'N/A')}, "
        f"IFSC: {ben.get('ifsc', ben.get('bic', 'N/A'))}, "
        f"Name: {ben.get('name', 'N/A')}"
    )

    # Determine queue
    queue = _determine_compliance_queue(failure_type, flags, amount)
    state["escalation_queue"] = queue

    # Generate escalation summary with LLM
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        temperature=0.1,
        api_key=config.OPENAI_API_KEY,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user",   USER_PROMPT),
    ])
    chain = prompt | llm

    try:
        response = chain.invoke({
            "exception_id":   state.get("exception_id"),
            "payment_id":     state.get("payment_id"),
            "client_id":      state.get("client_id"),
            "currency":       state.get("currency", "INR"),
            "amount":         amount,
            "payment_rail":   state.get("payment_rail"),
            "failure_type":   failure_type,
            "compliance_flags": flags or ["none"],
            "root_cause":     state.get("root_cause_summary", ""),
            "beneficiary_summary": ben_summary,
        })
        escalation_summary = response.content.strip()
    except Exception as exc:
        logger.error(f"  LLM escalation summary failed: {exc}", exc_info=True)
        escalation_summary = (
            f"COMPLIANCE ESCALATION — {state.get('exception_id')}\n\n"
            f"Payment {state.get('payment_id')} has been flagged for compliance review.\n"
            f"Amount: {state.get('currency', 'INR')} {amount:,.2f}\n"
            f"Flags: {flags}\n"
            f"Failure Type: {failure_type}\n\n"
            f"Assigned to: {queue}\n"
            f"Immediate review required. No automated action taken."
        )

    # Stub: In production, push to compliance case management system
    escalation_result = {
        "outcome":          "ESCALATED_TO_COMPLIANCE",
        "queue":            queue,
        "escalated_at":     datetime.utcnow().isoformat(),
        "escalation_summary": escalation_summary,
        "payment_locked":   True,
        "note": (
            f"Payment {state['payment_id']} locked from automated processing. "
            f"Assigned to {queue} (stubbed)."
        ),
    }

    state["execution_result"] = escalation_result
    state["client_message"]   = (
        f"Dear Valued Customer,\n\n"
        f"Your payment of {state.get('currency', 'INR')} {amount:,.2f} "
        f"(Reference: {state.get('payment_id', 'N/A')}) is currently under review "
        f"by our compliance team as part of our standard security procedures.\n\n"
        f"This review typically takes 1-3 business days. Your funds are safe and secure. "
        f"You will be notified once the review is complete.\n\n"
        f"Reference: {state.get('exception_id', 'N/A')}\n\n"
        f"For urgent assistance, please call 1800-XXX-XXXX.\n\n"
        f"Sincerely,\nFirst National Bank — Compliance & Security"
    )
    state["status"] = ExceptionStatus.ESCALATED.value

    # Audit entry
    state["audit_trail"].append(
        _make_audit(
            action="compliance_escalated",
            evidence=state.get("evidence_gathered", []) + ["compliance_flags"],
            decision=f"ESCALATED_TO:{queue}",
            justification=(
                f"Payment exception {state['exception_id']} escalated to {queue}. "
                f"Flags: {flags}. Amount: {state.get('currency')} {amount}. "
                f"Payment locked from retry."
            ),
        )
    )

    logger.info(
        f"[ComplianceAgent] Done. Escalated to {queue}. Status={state['status']}"
    )
    return state
