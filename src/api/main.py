"""
FastAPI REST API — Payment Exception Resolution Agent System.

Endpoints:
  POST /api/v1/exceptions/submit         — Submit a new payment exception
  POST /api/v1/exceptions/replay/{id}    — Replay an exception with new status
  GET  /api/v1/exceptions/{id}           — Get exception details
  GET  /api/v1/exceptions                — List exceptions (paginated, filtered)
  POST /api/v1/exceptions/{id}/override  — Operator override
  GET  /api/v1/metrics                   — System performance metrics
  GET  /health                           — Health check
"""

import logging
import uuid
import json
import asyncio
import threading
import queue as queue_module
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from src.workflow import app as workflow_app
from src.config import config
from src.models.state import (
    ExceptionStatus,
    FailureType,
    ResolutionAction,
    PaymentRail,
)
from src.utils.logger import setup_logging
from src.utils.metrics import ExceptionMetrics
from src.database.db import get_db, check_db_connection
from src.database.schema import init_db
from src.database.models import PaymentExceptionRecord, AuditLog

# Setup
setup_logging()
logger = logging.getLogger(__name__)
metrics = ExceptionMetrics()

# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

api_app = FastAPI(
    title="Payment Exception Resolution Agent",
    description=(
        "A production-grade multi-agent system for diagnosing, routing, "
        "and resolving failed banking payment transactions."
    ),
    version="2.0.0",
)

api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api_app.on_event("startup")
async def startup():
    """Initialise DB tables on startup."""
    try:
        init_db()
        logger.info("Database initialised on startup.")
    except Exception as exc:
        logger.error(f"DB init failed on startup: {exc}")


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class BeneficiaryDetails(BaseModel):
    account_no: Optional[str] = None
    ifsc:       Optional[str] = None
    iban:       Optional[str] = None
    bic:        Optional[str] = None
    upi_id:     Optional[str] = None
    name:       Optional[str] = None

    model_config = ConfigDict(extra="allow")


class ExceptionSubmitRequest(BaseModel):
    """Schema for submitting a new payment exception."""
    payment_id:         str   = Field(..., description="Original payment transaction ID")
    client_id:          str   = Field(..., description="Client / customer ID")
    account_id:         str   = Field(..., description="Source account ID")
    payment_rail:       str   = Field(..., description="Payment rail: NEFT/RTGS/IMPS/SWIFT/UPI/INTERNAL")
    payment_type:       str   = Field(..., description="domestic_transfer | wire | book_transfer | disbursement")
    amount:             float = Field(..., gt=0, description="Transaction amount")
    currency:           str   = Field(default="INR", description="ISO 4217 currency code")
    beneficiary_details: BeneficiaryDetails = Field(..., description="Beneficiary bank details")
    failure_code:       str   = Field(..., description="Error code from payment system")
    failure_message:    Optional[str] = Field(None, description="Human-readable error")
    submitted_at:       Optional[str] = Field(None, description="ISO 8601 original submission time")
    triggered_by:       Optional[str] = Field(default="system_event")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "payment_id":   "PAY-20240601-001",
                "client_id":    "CLT-4521",
                "account_id":   "ACC-10023456",
                "payment_rail": "NEFT",
                "payment_type": "domestic_transfer",
                "amount":       25000.00,
                "currency":     "INR",
                "beneficiary_details": {
                    "account_no": "123456789012",
                    "ifsc":       "HDFC0001234",
                    "name":       "Rajesh Kumar"
                },
                "failure_code":    "INVALID_IFSC",
                "failure_message": "IFSC code not found in directory",
                "submitted_at":    "2024-06-01T14:30:00",
                "triggered_by":    "system_event"
            }
        }
    )


class ReplayRequest(BaseModel):
    """Submit a replay / status update for an existing exception."""
    new_status_event: str = Field(..., description="New status information from downstream system")
    operator_id:      Optional[str] = Field(None, description="Operator submitting the replay")
    override_action:  Optional[str] = Field(None, description="Force a specific resolution action")


class OperatorOverrideRequest(BaseModel):
    """Operator manually overrides the system's resolution decision."""
    operator_id:     str = Field(..., description="Operator employee ID")
    override_action: str = Field(..., description="Forced resolution action")
    justification:   str = Field(..., description="Mandatory justification for override")


class ExceptionResponse(BaseModel):
    """Response returned after processing a payment exception."""
    exception_id:       str
    payment_id:         str
    status:             str
    failure_type:       str
    resolution_action:  Optional[str]
    decision_rationale: Optional[str]
    decision_confidence: Optional[float]
    escalation_queue:   Optional[str]
    client_message:     Optional[str]
    retry_count:        int
    audit_trail_length: int
    processing_time_s:  float
    submitted_at:       str
    resolved_at:        Optional[str] = None


class ExceptionDetailResponse(ExceptionResponse):
    """Full detail response with audit trail."""
    audit_trail:        List[Dict[str, Any]]
    execution_result:   Optional[Dict[str, Any]]
    compliance_flags:   List[str]
    balance_check:      Optional[Dict[str, Any]]
    network_status:     Optional[Dict[str, Any]]
    root_cause_summary: Optional[str]


class HealthResponse(BaseModel):
    status:      str
    version:     str
    timestamp:   str
    db_connected: bool


class MetricsResponse(BaseModel):
    total_exceptions:          int
    escalated_exceptions:      int
    auto_resolved:             int
    automation_rate_pct:       float
    escalation_rate_pct:       float
    average_response_time_s:   float
    failure_type_distribution: dict
    resolution_distribution:   dict


# ---------------------------------------------------------------------------
# Helper: build initial state
# ---------------------------------------------------------------------------

def _build_initial_state(req: ExceptionSubmitRequest, exception_id: str) -> dict:
    return {
        "exception_id":       exception_id,
        "payment_id":         req.payment_id,
        "client_id":          req.client_id,
        "account_id":         req.account_id,
        "payment_rail":       req.payment_rail,
        "payment_type":       req.payment_type,
        "amount":             req.amount,
        "currency":           req.currency,
        "beneficiary_details": req.beneficiary_details.model_dump(),
        "failure_code":       req.failure_code,
        "failure_message":    req.failure_message or "",
        "submitted_at":       req.submitted_at or datetime.utcnow().isoformat(),
        "triggered_by":       req.triggered_by or "system_event",
        # Investigation fields (populated by agents)
        "failure_type":       FailureType.UNKNOWN.value,
        "root_cause_summary": "",
        "prior_retry_records": [],
        "balance_check":      {},
        "beneficiary_valid":  True,
        "compliance_flags":   [],
        "network_status":     {},
        "duplicate_of":       None,
        "is_within_cutoff":   True,
        "evidence_gathered":  [],
        # Decision fields
        "resolution_action":  "",
        "decision_confidence": 0.0,
        "decision_rationale": "",
        "is_safe_to_automate": False,
        "retry_count":        0,
        "max_retries_allowed": config.MAX_RETRY_ATTEMPTS,
        # Execution fields
        "status":             ExceptionStatus.INGESTED.value,
        "execution_result":   {},
        "client_message":     "",
        "escalation_queue":   "",
        "scheduled_retry_at": None,
        # Audit fields
        "audit_trail":        [],
        "is_duplicate_event": False,
        "replay_of":          None,
        "operator_override":  None,
        "metadata":           {},
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@api_app.get("/", response_model=dict)
async def root():
    return {
        "system": "Payment Exception Resolution Agent",
        "version": "2.0.0",
        "description": (
            "Production-grade multi-agent system for failed payment transaction resolution."
        ),
        "endpoints": {
            "submit_exception":  "POST /api/v1/exceptions/submit",
            "get_exception":     "GET  /api/v1/exceptions/{exception_id}",
            "list_exceptions":   "GET  /api/v1/exceptions",
            "replay_exception":  "POST /api/v1/exceptions/{exception_id}/replay",
            "operator_override": "POST /api/v1/exceptions/{exception_id}/override",
            "metrics":           "GET  /api/v1/metrics",
            "health":            "GET  /health",
        },
    }


@api_app.get("/health", response_model=HealthResponse)
async def health_check():
    db_ok = check_db_connection()
    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        version="2.0.0",
        timestamp=datetime.utcnow().isoformat(),
        db_connected=db_ok,
    )


@api_app.post("/api/v1/exceptions/submit", response_model=ExceptionResponse)
async def submit_exception(req: ExceptionSubmitRequest):
    """
    Submit a new payment exception for multi-agent resolution.

    The exception flows through:
    ingestion → investigation → root_cause → decision → execution → egress
    """
    exception_id = f"{config.EXCEPTION_ID_PREFIX}-{uuid.uuid4().hex[:8].upper()}"
    logger.info(f"Received exception submission: {exception_id} for payment {req.payment_id}")

    initial_state = _build_initial_state(req, exception_id)
    start_time = datetime.utcnow()

    try:
        result = workflow_app.invoke(initial_state)
    except Exception as exc:
        logger.error(f"Workflow failed for {exception_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Exception processing failed: {str(exc)}"
        )

    processing_time = (datetime.utcnow() - start_time).total_seconds()

    # Track metrics
    metrics.record_exception(
        failure_type=result.get("failure_type", "UNKNOWN"),
        resolution_action=result.get("resolution_action", "UNKNOWN"),
        escalated=result.get("status") in (
            ExceptionStatus.ESCALATED.value,
            ExceptionStatus.AWAITING_INPUT.value,
        ),
        response_time=processing_time,
    )

    logger.info(
        f"Exception {exception_id} resolved: status={result.get('status')}, "
        f"action={result.get('resolution_action')}, time={processing_time:.2f}s"
    )

    return ExceptionResponse(
        exception_id=exception_id,
        payment_id=req.payment_id,
        status=result.get("status", ""),
        failure_type=result.get("failure_type", ""),
        resolution_action=result.get("resolution_action"),
        decision_rationale=result.get("decision_rationale"),
        decision_confidence=result.get("decision_confidence"),
        escalation_queue=result.get("escalation_queue") or None,
        client_message=result.get("client_message") or None,
        retry_count=result.get("retry_count", 0),
        audit_trail_length=len(result.get("audit_trail", [])),
        processing_time_s=round(processing_time, 3),
        submitted_at=result.get("submitted_at", ""),
        resolved_at=result.get("metadata", {}).get("processing_completed_at"),
    )


# ---------------------------------------------------------------------------
# SSE — Real-time agent progress stream
# ---------------------------------------------------------------------------

# Global registry: exception_id -> queue of SSE events
_sse_queues: Dict[str, queue_module.Queue] = {}
_sse_lock = threading.Lock()

AGENT_ORDER = [
    "ingestion_agent",
    "investigation_agent",
    "root_cause_agent",
    "decision_agent",
    "auto_resolve_agent",
    "client_outreach_agent",
    "compliance_agent",
    "manual_review_agent",
    "egress_agent",
]

AGENT_LABELS = {
    "ingestion_agent":       "Ingestion — Validating & normalising",
    "investigation_agent":   "Investigation — Gathering evidence",
    "root_cause_agent":      "Root Cause Analysis — Diagnosing failure",
    "decision_agent":        "Decision — Choosing resolution action",
    "auto_resolve_agent":    "Auto-Resolve — Executing automated action",
    "client_outreach_agent": "Client Outreach — Composing notification",
    "compliance_agent":      "Compliance — Escalating to review queue",
    "manual_review_agent":   "Manual Review — Packaging ops dossier",
    "egress_agent":          "Egress — Persisting & sealing audit trail",
}


def _push_event(exception_id: str, event_type: str, data: dict):
    """Push an SSE event to all listeners for this exception."""
    with _sse_lock:
        q = _sse_queues.get(exception_id)
    if q:
        q.put({"type": event_type, "data": data})


def _run_workflow_with_events(initial_state: dict, exception_id: str) -> dict:
    """
    Run the LangGraph workflow using stream_mode='updates' so we get
    per-node callbacks, and push SSE events for each agent step.
    """
    result_holder = {}

    # Push pipeline started
    _push_event(exception_id, "pipeline_start", {
        "exception_id": exception_id,
        "agents": AGENT_ORDER,
        "labels": AGENT_LABELS,
        "timestamp": datetime.utcnow().isoformat(),
    })

    try:
        # stream() yields {node_name: state_update} dicts after each node
        for chunk in workflow_app.stream(initial_state, stream_mode="updates"):
            for node_name, state_update in chunk.items():
                # Derive what this agent produced
                audit = (state_update.get("audit_trail") or [])
                last_audit = audit[-1] if audit else {}

                _push_event(exception_id, "agent_complete", {
                    "agent":        node_name,
                    "label":        AGENT_LABELS.get(node_name, node_name),
                    "decision":     last_audit.get("decision", ""),
                    "justification": last_audit.get("justification", "")[:200],
                    "failure_type": state_update.get("failure_type", ""),
                    "resolution_action": state_update.get("resolution_action", ""),
                    "status":       state_update.get("status", ""),
                    "timestamp":    datetime.utcnow().isoformat(),
                })
                result_holder.update(state_update)

    except Exception as exc:
        _push_event(exception_id, "pipeline_error", {
            "error": str(exc),
            "timestamp": datetime.utcnow().isoformat(),
        })
        raise

    # Push final done event
    _push_event(exception_id, "pipeline_done", {
        "exception_id":      exception_id,
        "failure_type":      result_holder.get("failure_type", ""),
        "resolution_action": result_holder.get("resolution_action", ""),
        "status":            result_holder.get("status", ""),
        "decision_confidence": result_holder.get("decision_confidence", 0),
        "decision_rationale": result_holder.get("decision_rationale", ""),
        "escalation_queue":  result_holder.get("escalation_queue", ""),
        "client_message":    result_holder.get("client_message", ""),
        "retry_count":       result_holder.get("retry_count", 0),
        "audit_trail_length": len(result_holder.get("audit_trail", [])),
        "timestamp":         datetime.utcnow().isoformat(),
    })

    # Signal stream end
    with _sse_lock:
        q = _sse_queues.get(exception_id)
    if q:
        q.put(None)  # sentinel

    return result_holder


@api_app.post("/api/v1/exceptions/submit-stream")
async def submit_exception_stream_init(req: ExceptionSubmitRequest):
    """
    Submit exception and get back an exception_id to connect the SSE stream to.
    The actual processing starts when the client connects to /stream/{exception_id}.
    """
    exception_id = f"{config.EXCEPTION_ID_PREFIX}-{uuid.uuid4().hex[:8].upper()}"
    initial_state = _build_initial_state(req, exception_id)

    # Register SSE queue before spawning thread
    q = queue_module.Queue()
    with _sse_lock:
        _sse_queues[exception_id] = q

    start_time = datetime.utcnow()

    def _run():
        try:
            result = _run_workflow_with_events(initial_state, exception_id)
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            metrics.record_exception(
                failure_type=result.get("failure_type", "UNKNOWN"),
                resolution_action=result.get("resolution_action", "UNKNOWN"),
                escalated=result.get("status") in (
                    ExceptionStatus.ESCALATED.value,
                    ExceptionStatus.AWAITING_INPUT.value,
                ),
                response_time=processing_time,
            )
        except Exception as exc:
            logger.error(f"Stream workflow error: {exc}", exc_info=True)
        finally:
            # Cleanup queue after 5 minutes
            import time
            time.sleep(300)
            with _sse_lock:
                _sse_queues.pop(exception_id, None)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return {"exception_id": exception_id, "stream_url": f"/api/v1/exceptions/{exception_id}/stream"}


@api_app.get("/api/v1/exceptions/{exception_id}/stream")
async def stream_exception_events(exception_id: str, request: Request):
    """
    SSE stream — emits real-time agent progress events for a running exception.
    Connect immediately after calling /submit-stream.
    """
    with _sse_lock:
        q = _sse_queues.get(exception_id)

    if q is None:
        raise HTTPException(status_code=404, detail="No active stream for this exception_id.")

    async def event_generator():
        yield "retry: 1000\n\n"
        while True:
            if await request.is_disconnected():
                break
            try:
                # Poll queue without blocking the event loop
                item = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: q.get(timeout=0.2)
                )
                if item is None:
                    # Stream complete
                    yield f"event: done\ndata: {{}}\n\n"
                    break
                payload = json.dumps(item["data"])
                yield f"event: {item['type']}\ndata: {payload}\n\n"
            except queue_module.Empty:
                # Send keepalive
                yield ": keepalive\n\n"
            except Exception:
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@api_app.get("/api/v1/exceptions/{exception_id}", response_model=ExceptionDetailResponse)
async def get_exception(exception_id: str, db: Session = Depends(get_db)):
    """Retrieve full details of a specific payment exception."""
    record = db.query(PaymentExceptionRecord).filter_by(
        exception_id=exception_id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail=f"Exception {exception_id} not found.")

    audit_entries = [
        {
            "agent":         a.agent,
            "action":        a.action,
            "decision":      a.decision,
            "justification": a.justification,
            "evidence_used": json.loads(a.evidence_used) if a.evidence_used else [],
            "timestamp":     a.created_at.isoformat() if a.created_at else None,
        }
        for a in sorted(record.audit_logs, key=lambda x: x.created_at or datetime.min)
    ]

    return ExceptionDetailResponse(
        exception_id=record.exception_id,
        payment_id=record.payment_id,
        status=record.status.value if record.status else "",
        failure_type=record.failure_type.value if record.failure_type else "",
        resolution_action=record.resolution_action.value if record.resolution_action else None,
        decision_rationale=record.decision_rationale,
        decision_confidence=record.decision_confidence,
        escalation_queue=record.escalation_queue,
        client_message=record.client_message,
        retry_count=record.retry_count,
        audit_trail_length=len(audit_entries),
        processing_time_s=0.0,
        submitted_at=record.submitted_at.isoformat() if record.submitted_at else "",
        resolved_at=record.resolved_at.isoformat() if record.resolved_at else None,
        audit_trail=audit_entries,
        execution_result=None,
        compliance_flags=record.get_compliance_flags(),
        balance_check=None,
        network_status=None,
        root_cause_summary=record.root_cause_summary,
    )


@api_app.get("/api/v1/exceptions", response_model=List[ExceptionResponse])
async def list_exceptions(
    status:       Optional[str] = Query(None, description="Filter by status"),
    failure_type: Optional[str] = Query(None, description="Filter by failure type"),
    payment_rail: Optional[str] = Query(None, description="Filter by rail"),
    limit:        int           = Query(50, ge=1, le=200),
    offset:       int           = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List payment exceptions with optional filters."""
    query = db.query(PaymentExceptionRecord)

    if status:
        query = query.filter(PaymentExceptionRecord.status == status)
    if failure_type:
        query = query.filter(PaymentExceptionRecord.failure_type == failure_type)
    if payment_rail:
        query = query.filter(PaymentExceptionRecord.payment_rail == payment_rail)

    records = query.order_by(
        PaymentExceptionRecord.created_at.desc()
    ).offset(offset).limit(limit).all()

    return [
        ExceptionResponse(
            exception_id=r.exception_id,
            payment_id=r.payment_id,
            status=r.status.value if r.status else "",
            failure_type=r.failure_type.value if r.failure_type else "",
            resolution_action=r.resolution_action.value if r.resolution_action else None,
            decision_rationale=r.decision_rationale,
            decision_confidence=r.decision_confidence,
            escalation_queue=r.escalation_queue,
            client_message=None,
            retry_count=r.retry_count,
            audit_trail_length=len(r.audit_logs),
            processing_time_s=0.0,
            submitted_at=r.submitted_at.isoformat() if r.submitted_at else "",
            resolved_at=r.resolved_at.isoformat() if r.resolved_at else None,
        )
        for r in records
    ]


@api_app.post("/api/v1/exceptions/{exception_id}/replay", response_model=ExceptionResponse)
async def replay_exception(
    exception_id: str,
    req: ReplayRequest,
    db: Session = Depends(get_db),
):
    """
    Replay an existing exception with new status information.
    Supports the 'feedback loop' requirement: re-evaluate after new events arrive.
    """
    record = db.query(PaymentExceptionRecord).filter_by(
        exception_id=exception_id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail=f"Exception {exception_id} not found.")

    logger.info(f"Replaying exception {exception_id}: {req.new_status_event}")

    # Build a replay state from the existing record
    replay_exception_id = f"{config.EXCEPTION_ID_PREFIX}-{uuid.uuid4().hex[:8].upper()}"
    initial_state = {
        "exception_id":       replay_exception_id,
        "payment_id":         record.payment_id,
        "client_id":          record.client_id,
        "account_id":         record.account_id,
        "payment_rail":       record.payment_rail.value if record.payment_rail else "INTERNAL",
        "payment_type":       record.payment_type,
        "amount":             record.amount,
        "currency":           record.currency,
        "beneficiary_details": record.get_beneficiary_details(),
        "failure_code":       record.failure_code or "RETRY_UNKNOWN",
        "failure_message":    f"Replay: {req.new_status_event}",
        "submitted_at":       record.submitted_at.isoformat() if record.submitted_at else datetime.utcnow().isoformat(),
        "triggered_by":       "replay",
        "failure_type":       FailureType.UNKNOWN.value,
        "root_cause_summary": "",
        "prior_retry_records": [],
        "balance_check":      {},
        "beneficiary_valid":  True,
        "compliance_flags":   [],
        "network_status":     {},
        "duplicate_of":       None,
        "is_within_cutoff":   True,
        "evidence_gathered":  [],
        "resolution_action":  req.override_action or "",
        "decision_confidence": 0.0,
        "decision_rationale": "",
        "is_safe_to_automate": False,
        "retry_count":        record.retry_count,
        "max_retries_allowed": record.max_retries_allowed,
        "status":             ExceptionStatus.INGESTED.value,
        "execution_result":   {},
        "client_message":     "",
        "escalation_queue":   "",
        "scheduled_retry_at": None,
        "audit_trail":        [],
        "is_duplicate_event": False,
        "replay_of":          exception_id,
        "operator_override":  None,
        "metadata":           {"replay_triggered_by": req.operator_id or "system"},
    }

    start_time = datetime.utcnow()
    try:
        result = workflow_app.invoke(initial_state)
    except Exception as exc:
        logger.error(f"Replay workflow failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Replay failed: {str(exc)}")

    processing_time = (datetime.utcnow() - start_time).total_seconds()

    return ExceptionResponse(
        exception_id=replay_exception_id,
        payment_id=record.payment_id,
        status=result.get("status", ""),
        failure_type=result.get("failure_type", ""),
        resolution_action=result.get("resolution_action"),
        decision_rationale=result.get("decision_rationale"),
        decision_confidence=result.get("decision_confidence"),
        escalation_queue=result.get("escalation_queue") or None,
        client_message=result.get("client_message") or None,
        retry_count=result.get("retry_count", 0),
        audit_trail_length=len(result.get("audit_trail", [])),
        processing_time_s=round(processing_time, 3),
        submitted_at=result.get("submitted_at", ""),
    )


@api_app.post("/api/v1/exceptions/{exception_id}/override")
async def operator_override(
    exception_id: str,
    req: OperatorOverrideRequest,
    db: Session = Depends(get_db),
):
    """
    Operator manually overrides the system's resolution decision.
    Records the override in the audit trail.
    """
    record = db.query(PaymentExceptionRecord).filter_by(
        exception_id=exception_id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail=f"Exception {exception_id} not found.")

    valid_actions = [r.value for r in ResolutionAction]
    if req.override_action not in valid_actions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid override_action. Valid values: {valid_actions}"
        )

    # Record the override
    override_data = {
        "operator_id":     req.operator_id,
        "override_action": req.override_action,
        "justification":   req.justification,
        "timestamp":       datetime.utcnow().isoformat(),
    }
    record.operator_override = json.dumps(override_data)
    record.resolution_action = req.override_action
    record.updated_at        = datetime.utcnow()

    # Add audit log entry
    audit = AuditLog(
        exception_id=exception_id,
        agent="operator_override",
        action="manual_override",
        decision=req.override_action,
        justification=(
            f"Operator {req.operator_id} overrode resolution to {req.override_action}. "
            f"Reason: {req.justification}"
        ),
        evidence_used=json.dumps(["operator_decision"]),
    )
    db.add(audit)
    db.commit()

    logger.info(
        f"Operator {req.operator_id} overrode exception {exception_id} "
        f"to {req.override_action}"
    )

    return {
        "message":       "Override applied successfully.",
        "exception_id":  exception_id,
        "override":      override_data,
    }


@api_app.get("/api/v1/metrics", response_model=MetricsResponse)
async def get_metrics():
    """System performance metrics (in-memory, since last restart)."""
    m = metrics.get_metrics()
    return MetricsResponse(
        total_exceptions=m["total_exceptions"],
        escalated_exceptions=m["escalated_exceptions"],
        auto_resolved=m["auto_resolved"],
        automation_rate_pct=m["automation_rate_pct"],
        escalation_rate_pct=m["escalation_rate_pct"],
        average_response_time_s=m["average_response_time_s"],
        failure_type_distribution=m["failure_type_distribution"],
        resolution_distribution=m["resolution_distribution"],
    )


@api_app.post("/api/v1/metrics/reset")
async def reset_metrics():
    metrics.reset()
    return {"message": "Metrics reset."}


if __name__ == "__main__":
    import uvicorn
    config.validate()
    uvicorn.run(
        "src.api.main:api_app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,
        log_level=config.LOG_LEVEL.lower(),
    )
