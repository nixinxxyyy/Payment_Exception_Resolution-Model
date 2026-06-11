import React from 'react'

const STATUS_CONFIG = {
  RESOLVED:     { label: 'Resolved',     bg: '#dcfce7', color: '#15803d', border: '#86efac' },
  ESCALATED:    { label: 'Escalated',    bg: '#fee2e2', color: '#b91c1c', border: '#fca5a5' },
  INVESTIGATING:{ label: 'Investigating',bg: '#fef3c7', color: '#92400e', border: '#fcd34d' },
  DECIDED:      { label: 'Decided',      bg: '#dbeafe', color: '#1d4ed8', border: '#93c5fd' },
  HELD:         { label: 'Held',         bg: '#ede9fe', color: '#5b21b6', border: '#c4b5fd' },
  AWAITING_INPUT:{ label: 'Awaiting Input', bg: '#cffafe', color: '#0e7490', border: '#67e8f9' },
  EXECUTING:    { label: 'Executing',    bg: '#d1fae5', color: '#065f46', border: '#6ee7b7' },
  CANCELLED:    { label: 'Cancelled',    bg: '#f3f4f6', color: '#374151', border: '#d1d5db' },
  INGESTED:     { label: 'Ingested',     bg: '#f0fdf4', color: '#166534', border: '#bbf7d0' },
}

const FAILURE_CONFIG = {
  INCORRECT_BENEFICIARY:  { label: 'Wrong Beneficiary', color: '#b45309', bg: '#fef3c7' },
  INSUFFICIENT_FUNDS:     { label: 'Insufficient Funds',color: '#dc2626', bg: '#fee2e2' },
  DUPLICATE_PAYMENT:      { label: 'Duplicate',          color: '#7c3aed', bg: '#ede9fe' },
  COMPLIANCE_HOLD:        { label: 'Compliance Hold',    color: '#9f1239', bg: '#ffe4e6' },
  NETWORK_RAIL_FAILURE:   { label: 'Network Failure',    color: '#1d4ed8', bg: '#dbeafe' },
  CUTOFF_TIME_MISS:       { label: 'Cut-off Missed',     color: '#0e7490', bg: '#cffafe' },
  UNCERTAIN_RETRY_STATUS: { label: 'Uncertain Retry',    color: '#6b7280', bg: '#f3f4f6' },
  UNKNOWN:                { label: 'Unknown',             color: '#6b7280', bg: '#f3f4f6' },
}

const ACTION_CONFIG = {
  AUTO_RETRY:         { label: 'Auto Retry',       color: '#065f46', bg: '#d1fae5' },
  AUTO_CORRECT:       { label: 'Auto Correct',     color: '#065f46', bg: '#d1fae5' },
  CLIENT_OUTREACH:    { label: 'Client Outreach',  color: '#0e7490', bg: '#cffafe' },
  COMPLIANCE_REVIEW:  { label: 'Compliance',       color: '#9f1239', bg: '#ffe4e6' },
  HOLD_FOR_WINDOW:    { label: 'Hold for Window',  color: '#5b21b6', bg: '#ede9fe' },
  CANCEL:             { label: 'Cancelled',         color: '#374151', bg: '#f3f4f6' },
  MANUAL_REVIEW:      { label: 'Manual Review',    color: '#92400e', bg: '#fef3c7' },
  DUPLICATE_SUPPRESS: { label: 'Dup. Suppressed',  color: '#7c3aed', bg: '#ede9fe' },
}

const baseStyle = {
  display: 'inline-flex',
  alignItems: 'center',
  padding: '3px 10px',
  borderRadius: '9999px',
  fontSize: '12px',
  fontWeight: 600,
  letterSpacing: '0.3px',
  border: '1px solid transparent',
  whiteSpace: 'nowrap',
}

export function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG['INGESTED']
  return (
    <span
      style={{ ...baseStyle, background: cfg.bg, color: cfg.color, borderColor: cfg.border }}
      aria-label={`Status: ${cfg.label}`}
    >
      {cfg.label}
    </span>
  )
}

export function FailureBadge({ type }) {
  const cfg = FAILURE_CONFIG[type] || FAILURE_CONFIG['UNKNOWN']
  return (
    <span
      style={{ ...baseStyle, background: cfg.bg, color: cfg.color }}
      aria-label={`Failure type: ${cfg.label}`}
    >
      {cfg.label}
    </span>
  )
}

export function ActionBadge({ action }) {
  const cfg = ACTION_CONFIG[action] || { label: action, color: '#374151', bg: '#f3f4f6' }
  return (
    <span
      style={{ ...baseStyle, background: cfg.bg, color: cfg.color }}
      aria-label={`Resolution action: ${cfg.label}`}
    >
      {cfg.label}
    </span>
  )
}
