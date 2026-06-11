"""
Client Outreach Agent — Generates and queues a client notification.

Handles: CLIENT_OUTREACH

Uses GPT-4o to compose a professional, empathetic banking communication
explaining the exception and requesting the necessary client action.

In production, the message would be delivered via the bank's notification
service (email, SMS, push notification, or secure message centre).
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
        "agent": "client_outreach_agent",
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "evidence_used": evidence,
        "decision": decision,
        "justification": justification,
    }


SYSTEM_PROMPT = """You are a customer communication specialist at a premium bank.
Write a professional, empathetic, and clear message to a banking customer about
a failed payment transaction. The message should:

1. Address the customer respectfully (use "Dear Valued Customer" if no name available)
2. Briefly explain what happened without jargon
3. Clearly state what the customer needs to do (if anything)
4. Provide a reference number
5. Reassure the customer their funds are safe
6. End with bank contact information (use placeholder)

Tone: Professional, warm, reassuring. No technical jargon.
Length: 150-250 words.
Format: Plain text, suitable for email or secure message centre."""

USER_PROMPT = """Failure Type: {failure_type}
Amount: {currency} {amount}
Payment Reference: {payment_id}
Exception Reference: {exception_id}
Client ID: {client_id}
Root Cause Summary: {root_cause}
Required Client Action: {action_required}

Draft the client communication:"""


# Maps failure type → plain English action required from client
CLIENT_ACTION_MAP = {
    FailureType.INSUFFICIENT_FUNDS.value: (
        "Please ensure sufficient funds are available in your account and "
        "re-initiate the transfer, or contact us to arrange an overdraft facility."
    ),
    FailureType.INCORRECT_BENEFICIARY.value: (
        "Please verify the beneficiary's account details (account number, IFSC code, "
        "or UPI ID) and re-submit the payment with the correct information."
    ),
    FailureType.COMPLIANCE_HOLD.value: (
        "Your payment is under review by our compliance team. No action is required "
        "from you at this time. We will contact you if additional documentation is needed."
    ),
    FailureType.UNKNOWN.value: (
        "Our team is investigating this issue. We will provide an update within "
        "2 business days. No action is required from you at this time."
    ),
}


def client_outreach_agent(state: PaymentExceptionState) -> PaymentExceptionState:
    """
    Generate a client notification for the payment exception.

    Mutates: client_message, status → AWAITING_INPUT
    """
    logger.info(f"[ClientOutreachAgent] Composing message for {state['exception_id']}")

    failure_type = state.get("failure_type", FailureType.UNKNOWN.value)
    action_required = CLIENT_ACTION_MAP.get(
        failure_type,
        "Please contact our support team for assistance with this payment."
    )

    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        temperature=0.6,   # Slightly creative for natural language
        api_key=config.OPENAI_API_KEY,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user",   USER_PROMPT),
    ])
    chain = prompt | llm

    try:
        response = chain.invoke({
            "failure_type":  failure_type,
            "currency":      state.get("currency", "INR"),
            "amount":        state.get("amount", 0),
            "payment_id":    state.get("payment_id", ""),
            "exception_id":  state.get("exception_id", ""),
            "client_id":     state.get("client_id", ""),
            "root_cause":    state.get("root_cause_summary", "Payment could not be processed."),
            "action_required": action_required,
        })
        client_message = response.content.strip()
    except Exception as exc:
        logger.error(f"  LLM message generation failed: {exc}", exc_info=True)
        client_message = (
            f"Dear Valued Customer,\n\n"
            f"We regret to inform you that your payment of "
            f"{state.get('currency', 'INR')} {state.get('amount', 0):,.2f} "
            f"(Reference: {state.get('payment_id', 'N/A')}) could not be processed.\n\n"
            f"{action_required}\n\n"
            f"Your exception reference number is: {state.get('exception_id', 'N/A')}.\n"
            f"Your funds remain safe and will not be deducted until the payment succeeds.\n\n"
            f"For assistance, please call our 24x7 helpline: 1800-XXX-XXXX.\n\n"
            f"Sincerely,\nFirst National Bank — Customer Support"
        )

    # Stub: In production, enqueue to notification service
    notification_result = {
        "channel":    "email",
        "queued_at":  datetime.utcnow().isoformat(),
        "client_id":  state.get("client_id"),
        "status":     "QUEUED",
        "note":       "Message queued for delivery via bank notification service (stubbed).",
    }

    state["client_message"]  = client_message
    state["execution_result"] = notification_result
    state["status"]           = ExceptionStatus.AWAITING_INPUT.value

    # Audit entry
    state["audit_trail"].append(
        _make_audit(
            action="client_notified",
            evidence=["client_outreach_required", "failure_type", "root_cause_summary"],
            decision="CLIENT_OUTREACH_QUEUED",
            justification=(
                f"Client {state['client_id']} notified about exception {state['exception_id']}. "
                f"Failure: {failure_type}. Action required: {action_required[:80]}..."
            ),
        )
    )

    logger.info(
        f"[ClientOutreachAgent] Done. Status={state['status']}, "
        f"message_length={len(client_message)} chars"
    )
    return state
