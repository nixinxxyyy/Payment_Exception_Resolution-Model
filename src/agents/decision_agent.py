"""
Decision Agent — Determines the resolution action and records its basis.

Uses a rule-based decision tree augmented by LLM reasoning for ambiguous cases.
Produces:
  - resolution_action (one of ResolutionAction enum values)
  - decision_rationale (human-readable, auditable justification)
  - updates status to DECIDED
"""

import logging
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.models.state import (
    PaymentExceptionState,
    FailureType,
    ResolutionAction,
    ExceptionStatus,
)
from src.config import config

logger = logging.getLogger(__name__)


def _make_audit(action: str, evidence: list, decision: str, justification: str) -> dict:
    return {
        "agent": "decision_agent",
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "evidence_used": evidence,
        "decision": decision,
        "justification": justification,
    }


SYSTEM_PROMPT = """You are a payment operations decision engine at a bank.
Given a diagnosed payment exception, choose exactly ONE resolution action.

RESOLUTION ACTIONS:
- AUTO_RETRY          : Retry the payment automatically (only if safe and no ambiguity)
- AUTO_CORRECT        : Correct minor beneficiary detail and retry automatically
- CLIENT_OUTREACH     : Contact the client to get missing or corrected information
- COMPLIANCE_REVIEW   : Route to compliance team — do NOT retry automatically
- HOLD_FOR_WINDOW     : Requeue for next processing window (cut-off missed)
- CANCEL              : Cancel payment and return funds to sender
- MANUAL_REVIEW       : Ops team must investigate before any action
- DUPLICATE_SUPPRESS  : Safely suppress the duplicate; ensure original is complete

DECISION RULES:
1. COMPLIANCE_HOLD → always COMPLIANCE_REVIEW
2. UNCERTAIN_RETRY_STATUS → always MANUAL_REVIEW  
3. INSUFFICIENT_FUNDS → CLIENT_OUTREACH (low balance notification)
4. DUPLICATE_PAYMENT → DUPLICATE_SUPPRESS (if original succeeded) else MANUAL_REVIEW
5. NETWORK_RAIL_FAILURE, network UP → AUTO_RETRY (if retry_count < max)
6. NETWORK_RAIL_FAILURE, network DOWN → HOLD_FOR_WINDOW
7. CUTOFF_TIME_MISS → HOLD_FOR_WINDOW
8. INCORRECT_BENEFICIARY, minor format → AUTO_CORRECT
9. INCORRECT_BENEFICIARY, major mismatch → CLIENT_OUTREACH
10. retry_count >= max_retries → MANUAL_REVIEW regardless of failure type

Respond in JSON only:
{{"resolution_action": "ACTION_VALUE", "rationale": "..."}}"""

USER_PROMPT = """Failure Type: {failure_type}
Failure Code: {failure_code}
Safe to Automate: {is_safe_to_automate}
Confidence: {confidence}
Retry Count: {retry_count} / {max_retries}
Network Status: {network_status}
Balance Sufficient: {balance_sufficient}
Compliance Flags: {compliance_flags}
Duplicate Of: {duplicate_of}
Within Cut-off: {is_within_cutoff}
Beneficiary Valid: {beneficiary_valid}
Amount: {currency} {amount}
Root Cause: {root_cause_summary}

Choose the resolution action:"""


def _rule_based_decision(state: PaymentExceptionState) -> str | None:
    """
    Deterministic rule-based decision for clear-cut cases.
    Returns a ResolutionAction string or None (fall through to LLM).
    """
    ft      = state.get("failure_type", FailureType.UNKNOWN.value)
    retries = state.get("retry_count", 0)
    max_r   = state.get("max_retries_allowed", config.MAX_RETRY_ATTEMPTS)
    flags   = state.get("compliance_flags") or []
    net     = (state.get("network_status") or {}).get("status", "UNKNOWN")
    bal     = (state.get("balance_check") or {}).get("sufficient", True)

    # Hard stops
    if flags:
        return ResolutionAction.COMPLIANCE_REVIEW.value

    if retries >= max_r:
        return ResolutionAction.MANUAL_REVIEW.value

    if ft == FailureType.COMPLIANCE_HOLD.value:
        return ResolutionAction.COMPLIANCE_REVIEW.value

    if ft == FailureType.UNCERTAIN_RETRY_STATUS.value:
        return ResolutionAction.MANUAL_REVIEW.value

    if ft == FailureType.INSUFFICIENT_FUNDS.value:
        return ResolutionAction.CLIENT_OUTREACH.value

    if ft == FailureType.DUPLICATE_PAYMENT.value:
        return ResolutionAction.DUPLICATE_SUPPRESS.value

    if ft == FailureType.CUTOFF_TIME_MISS.value:
        return ResolutionAction.HOLD_FOR_WINDOW.value

    if ft == FailureType.NETWORK_RAIL_FAILURE.value:
        if net == "UP":
            return ResolutionAction.AUTO_RETRY.value
        return ResolutionAction.HOLD_FOR_WINDOW.value

    # Return None to let LLM decide for ambiguous cases
    return None


def decision_agent(state: PaymentExceptionState) -> PaymentExceptionState:
    """
    Determine the resolution action for the payment exception.

    Applies deterministic rules first; defers to LLM for ambiguous cases.
    Mutates: resolution_action, decision_rationale, status.
    """
    logger.info(f"[DecisionAgent] Deciding for {state['exception_id']}")

    # ------------------------------------------------------------------
    # 1. Try rule-based decision first
    # ------------------------------------------------------------------
    rule_action = _rule_based_decision(state)

    if rule_action:
        action   = rule_action
        rationale = (
            f"Rule-based decision: {action} determined for failure type "
            f"'{state['failure_type']}'. "
            f"Network: {(state.get('network_status') or {}).get('status', 'N/A')}, "
            f"Retries: {state.get('retry_count', 0)}/{state.get('max_retries_allowed', 3)}, "
            f"Compliance flags: {state.get('compliance_flags') or 'none'}."
        )
        logger.info(f"  Rule-based decision: {action}")
    else:
        # ------------------------------------------------------------------
        # 2. LLM-assisted decision for ambiguous cases
        # ------------------------------------------------------------------
        logger.info("  Falling through to LLM for ambiguous case.")
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
                "failure_type":     state.get("failure_type", "UNKNOWN"),
                "failure_code":     state.get("failure_code", ""),
                "is_safe_to_automate": state.get("is_safe_to_automate", False),
                "confidence":       state.get("decision_confidence", 0.5),
                "retry_count":      state.get("retry_count", 0),
                "max_retries":      state.get("max_retries_allowed", config.MAX_RETRY_ATTEMPTS),
                "network_status":   (state.get("network_status") or {}).get("status", "UNKNOWN"),
                "balance_sufficient": (state.get("balance_check") or {}).get("sufficient", "unknown"),
                "compliance_flags": state.get("compliance_flags") or "none",
                "duplicate_of":     state.get("duplicate_of") or "none",
                "is_within_cutoff": state.get("is_within_cutoff", True),
                "beneficiary_valid": state.get("beneficiary_valid", True),
                "currency":         state.get("currency", "INR"),
                "amount":           state.get("amount", 0),
                "root_cause_summary": state.get("root_cause_summary", ""),
            })

            import json
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            parsed   = json.loads(raw)
            action   = parsed.get("resolution_action", ResolutionAction.MANUAL_REVIEW.value).upper()
            rationale = parsed.get("rationale", "LLM-determined resolution.")

            # Validate
            valid_actions = [r.value for r in ResolutionAction]
            if action not in valid_actions:
                action = ResolutionAction.MANUAL_REVIEW.value
                rationale += " (action normalised to MANUAL_REVIEW after invalid LLM output)"

        except Exception as exc:
            logger.error(f"  LLM decision failed: {exc}", exc_info=True)
            action    = ResolutionAction.MANUAL_REVIEW.value
            rationale = f"LLM decision failed ({exc}). Defaulting to manual review for safety."

    # ------------------------------------------------------------------
    # 3. Safety override: if LLM says AUTO_RETRY but not safe, downgrade
    # ------------------------------------------------------------------
    if action in (
        ResolutionAction.AUTO_RETRY.value,
        ResolutionAction.AUTO_CORRECT.value,
    ) and not state.get("is_safe_to_automate"):
        original_action = action
        action = ResolutionAction.MANUAL_REVIEW.value
        rationale = (
            f"Decision downgraded from {original_action} to MANUAL_REVIEW: "
            "automated execution not safe given current evidence. "
            + rationale
        )
        logger.warning(f"  Auto-action downgraded to MANUAL_REVIEW (safety override)")

    # ------------------------------------------------------------------
    # 4. Update state
    # ------------------------------------------------------------------
    state["resolution_action"] = action
    state["decision_rationale"] = rationale
    state["status"] = ExceptionStatus.DECIDED.value

    # ------------------------------------------------------------------
    # 5. Audit entry
    # ------------------------------------------------------------------
    state["audit_trail"].append(
        _make_audit(
            action="resolution_decided",
            evidence=state.get("evidence_gathered", []),
            decision=action,
            justification=rationale,
        )
    )

    logger.info(f"[DecisionAgent] Done. resolution_action={action}")
    return state
