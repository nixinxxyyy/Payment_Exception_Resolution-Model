"""
SQLAlchemy ORM models for MySQL persistence.

Tables:
    payment_exceptions   - Master case record for each exception
    audit_logs           - Immutable append-only audit trail
    retry_attempts       - Each retry attempt per exception
    client_notifications - Outreach messages sent to clients
"""

import json
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Boolean, Integer,
    DateTime, Text, ForeignKey, Enum as SAEnum,
    Index
)
from sqlalchemy.orm import relationship

from src.database.db import Base
from src.models.state import (
    FailureType, ResolutionAction, ExceptionStatus, PaymentRail
)


class PaymentExceptionRecord(Base):
    """Master record for a payment exception case."""
    __tablename__ = "payment_exceptions"

    # Primary key
    exception_id    = Column(String(32), primary_key=True, index=True)

    # Payment identifiers
    payment_id      = Column(String(64), nullable=False, index=True)
    client_id       = Column(String(64), nullable=False, index=True)
    account_id      = Column(String(64), nullable=False)

    # Payment details
    payment_rail    = Column(SAEnum(PaymentRail), nullable=False)
    payment_type    = Column(String(32), nullable=False)
    amount          = Column(Float, nullable=False)
    currency        = Column(String(8), nullable=False, default="INR")
    beneficiary_details = Column(Text, nullable=True)   # JSON blob

    # Failure info
    failure_code    = Column(String(64), nullable=True)
    failure_message = Column(Text, nullable=True)
    failure_type    = Column(
        SAEnum(FailureType), nullable=False, default=FailureType.UNKNOWN
    )

    # Resolution
    resolution_action   = Column(
        SAEnum(ResolutionAction), nullable=True
    )
    decision_confidence = Column(Float, default=0.0)
    decision_rationale  = Column(Text, nullable=True)
    status              = Column(
        SAEnum(ExceptionStatus),
        nullable=False,
        default=ExceptionStatus.INGESTED
    )

    # Retry tracking
    retry_count         = Column(Integer, default=0)
    max_retries_allowed = Column(Integer, default=3)

    # Escalation / outreach
    escalation_queue    = Column(String(64), nullable=True)
    client_message      = Column(Text, nullable=True)
    scheduled_retry_at  = Column(DateTime, nullable=True)

    # Investigation flags
    beneficiary_valid   = Column(Boolean, default=True)
    is_within_cutoff    = Column(Boolean, default=True)
    duplicate_of        = Column(String(64), nullable=True)
    compliance_flags    = Column(Text, nullable=True)    # JSON list
    root_cause_summary  = Column(Text, nullable=True)

    # Deduplication
    is_duplicate_event  = Column(Boolean, default=False)
    replay_of           = Column(String(32), nullable=True)
    triggered_by        = Column(String(32), default="system_event")

    # Operator override
    operator_override   = Column(Text, nullable=True)   # JSON blob

    # Timestamps
    submitted_at        = Column(DateTime, nullable=False)
    created_at          = Column(DateTime, default=datetime.utcnow)
    updated_at          = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    resolved_at         = Column(DateTime, nullable=True)

    # Relationships
    audit_logs          = relationship(
        "AuditLog", back_populates="exception", cascade="all, delete-orphan"
    )
    retry_attempts      = relationship(
        "RetryAttempt", back_populates="exception", cascade="all, delete-orphan"
    )
    client_notifications = relationship(
        "ClientNotification", back_populates="exception", cascade="all, delete-orphan"
    )

    # Compound indexes for performance
    __table_args__ = (
        Index("ix_payment_client", "payment_id", "client_id"),
        Index("ix_status_rail", "status", "payment_rail"),
    )

    def get_beneficiary_details(self) -> dict:
        if self.beneficiary_details:
            return json.loads(self.beneficiary_details)
        return {}

    def set_beneficiary_details(self, details: dict):
        self.beneficiary_details = json.dumps(details)

    def get_compliance_flags(self) -> list:
        if self.compliance_flags:
            return json.loads(self.compliance_flags)
        return []

    def set_compliance_flags(self, flags: list):
        self.compliance_flags = json.dumps(flags)


class AuditLog(Base):
    """Immutable audit log entry — never updated, only appended."""
    __tablename__ = "audit_logs"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    exception_id    = Column(
        String(32), ForeignKey("payment_exceptions.exception_id"), nullable=False
    )
    agent           = Column(String(64), nullable=False)
    action          = Column(String(128), nullable=False)
    decision        = Column(String(64), nullable=True)
    justification   = Column(Text, nullable=True)
    evidence_used   = Column(Text, nullable=True)   # JSON list
    created_at      = Column(DateTime, default=datetime.utcnow)

    exception       = relationship("PaymentExceptionRecord", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_exception", "exception_id"),
        Index("ix_audit_agent", "agent"),
    )


class RetryAttempt(Base):
    """Tracks each retry attempt for a payment exception."""
    __tablename__ = "retry_attempts"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    exception_id    = Column(
        String(32), ForeignKey("payment_exceptions.exception_id"), nullable=False
    )
    attempt_number  = Column(Integer, nullable=False)
    outcome         = Column(String(32), nullable=False)  # SUCCESS|FAILED|PENDING|UNKNOWN
    error_code      = Column(String(64), nullable=True)
    error_message   = Column(Text, nullable=True)
    attempted_at    = Column(DateTime, default=datetime.utcnow)

    exception       = relationship("PaymentExceptionRecord", back_populates="retry_attempts")

    __table_args__ = (
        Index("ix_retry_exception", "exception_id"),
    )


class ClientNotification(Base):
    """Records outreach messages sent to clients."""
    __tablename__ = "client_notifications"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    exception_id    = Column(
        String(32), ForeignKey("payment_exceptions.exception_id"), nullable=False
    )
    client_id       = Column(String(64), nullable=False)
    channel         = Column(String(32), default="email")  # email | sms | push
    message         = Column(Text, nullable=False)
    sent_at         = Column(DateTime, default=datetime.utcnow)
    response        = Column(Text, nullable=True)       # client's reply
    response_at     = Column(DateTime, nullable=True)

    exception       = relationship("PaymentExceptionRecord", back_populates="client_notifications")

    __table_args__ = (
        Index("ix_notif_exception", "exception_id"),
        Index("ix_notif_client", "client_id"),
    )
