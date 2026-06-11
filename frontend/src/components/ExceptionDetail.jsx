import React, { useEffect, useState } from 'react'
import { ChevronLeft, RefreshCw, AlertTriangle, CheckCircle, Clock, Shield } from 'lucide-react'
import { api } from '../api.js'
import { StatusBadge, FailureBadge, ActionBadge } from './StatusBadge.jsx'
import styles from './ExceptionDetail.module.css'

const AGENT_ICONS = {
  ingestion_agent:       '📥',
  investigation_agent:   '🔍',
  root_cause_agent:      '🧠',
  decision_agent:        '⚖️',
  auto_resolve_agent:    '🤖',
  client_outreach_agent: '📧',
  compliance_agent:      '🛡️',
  manual_review_agent:   '👤',
  egress_agent:          '📤',
  operator_override:     '🔑',
}

export default function ExceptionDetail({ exceptionId, navigate, VIEWS }) {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  const [replayForm,    setReplayForm]    = useState({ new_status_event: '', operator_id: '' })
  const [overrideForm,  setOverrideForm]  = useState({ operator_id: '', override_action: '', justification: '' })
  const [replayResult,  setReplayResult]  = useState(null)
  const [replayLoading, setReplayLoading] = useState(false)
  const [overrideResult, setOverrideResult] = useState(null)
  const [overrideLoading, setOverrideLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const d = await api.getException(exceptionId)
      setData(d)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [exceptionId])

  const submitReplay = async (e) => {
    e.preventDefault()
    setReplayLoading(true)
    setReplayResult(null)
    try {
      const r = await api.replayException(exceptionId, replayForm)
      setReplayResult(r)
    } catch (err) {
      setReplayResult({ error: err.message })
    } finally {
      setReplayLoading(false)
    }
  }

  const submitOverride = async (e) => {
    e.preventDefault()
    setOverrideLoading(true)
    setOverrideResult(null)
    try {
      const r = await api.overrideException(exceptionId, overrideForm)
      setOverrideResult(r)
      load()
    } catch (err) {
      setOverrideResult({ error: err.message })
    } finally {
      setOverrideLoading(false)
    }
  }

  if (loading) return (
    <div className={styles.loading} aria-busy="true">
      <span className={styles.spinner} aria-hidden="true" /> Loading exception details...
    </div>
  )

  if (error) return (
    <div className={styles.error} role="alert">
      <AlertTriangle size={18} /> Error: {error}
    </div>
  )

  if (!data) return null

  const tabs = ['overview', 'audit_trail', 'replay', 'override']

  return (
    <div className={styles.root}>
      {/* Back + header */}
      <div className={styles.topBar}>
        <button
          className={styles.backBtn}
          onClick={() => navigate(VIEWS.LIST)}
          aria-label="Back to exception list"
        >
          <ChevronLeft size={16} /> Back
        </button>
        <button className={styles.refreshBtn} onClick={load} aria-label="Refresh">
          <RefreshCw size={14} />
        </button>
      </div>

      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.title}>
            <code className={styles.excId}>{data.exception_id}</code>
          </h1>
          <p className={styles.payId}>Payment ID: <code>{data.payment_id}</code></p>
        </div>
        <div className={styles.badgeRow}>
          <StatusBadge status={data.status} />
          <FailureBadge type={data.failure_type} />
          {data.resolution_action && <ActionBadge action={data.resolution_action} />}
        </div>
      </div>

      {/* Tabs */}
      <div className={styles.tabBar} role="tablist" aria-label="Exception detail sections">
        {tabs.map((t) => (
          <button
            key={t}
            role="tab"
            aria-selected={activeTab === t}
            className={`${styles.tab} ${activeTab === t ? styles.activeTab : ''}`}
            onClick={() => setActiveTab(t)}
          >
            {t === 'overview'     && <CheckCircle  size={13} aria-hidden="true" />}
            {t === 'audit_trail'  && <Clock        size={13} aria-hidden="true" />}
            {t === 'replay'       && <RefreshCw    size={13} aria-hidden="true" />}
            {t === 'override'     && <Shield       size={13} aria-hidden="true" />}
            {t.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
          </button>
        ))}
      </div>

      {/* Overview tab */}
      {activeTab === 'overview' && (
        <div className={styles.overviewGrid}>
          <InfoCard title="Decision">
            <InfoRow label="Resolution Action"><ActionBadge action={data.resolution_action} /></InfoRow>
            <InfoRow label="Confidence">{Math.round((data.decision_confidence || 0) * 100)}%</InfoRow>
            <InfoRow label="Retry Count">{data.retry_count}</InfoRow>
            <InfoRow label="Escalation Queue">{data.escalation_queue || '—'}</InfoRow>
          </InfoCard>

          <InfoCard title="Root Cause">
            <p className={styles.rootCause}>{data.root_cause_summary || 'Pending investigation.'}</p>
          </InfoCard>

          <InfoCard title="Decision Rationale" fullWidth>
            <p className={styles.rootCause}>{data.decision_rationale || '—'}</p>
          </InfoCard>

          {data.compliance_flags?.length > 0 && (
            <InfoCard title="Compliance Flags" fullWidth>
              <ul className={styles.flagList}>
                {data.compliance_flags.map((f, i) => (
                  <li key={i} className={styles.flag}>🚩 {f}</li>
                ))}
              </ul>
            </InfoCard>
          )}

          {data.client_message && (
            <InfoCard title="Client Communication" fullWidth>
              <pre className={styles.clientMsg}>{data.client_message}</pre>
            </InfoCard>
          )}

          <InfoCard title="Timestamps">
            <InfoRow label="Submitted">{data.submitted_at ? new Date(data.submitted_at).toLocaleString('en-IN') : '—'}</InfoRow>
            <InfoRow label="Resolved">{data.resolved_at  ? new Date(data.resolved_at).toLocaleString('en-IN')  : '—'}</InfoRow>
          </InfoCard>

          <InfoCard title="Audit Summary">
            <InfoRow label="Total Entries">{data.audit_trail_length}</InfoRow>
          </InfoCard>
        </div>
      )}

      {/* Audit Trail tab */}
      {activeTab === 'audit_trail' && (
        <div className={styles.auditTrail} aria-label="Audit trail">
          {data.audit_trail?.length === 0 && (
            <p className={styles.empty}>No audit entries yet.</p>
          )}
          {data.audit_trail?.map((entry, i) => (
            <div key={i} className={styles.auditEntry}>
              <div className={styles.auditLeft}>
                <span className={styles.auditIcon} aria-hidden="true">
                  {AGENT_ICONS[entry.agent] || '📋'}
                </span>
                <div className={styles.auditLine} aria-hidden="true" />
              </div>
              <div className={styles.auditContent}>
                <div className={styles.auditHeader}>
                  <strong className={styles.auditAgent}>{entry.agent}</strong>
                  <span className={styles.auditTime}>
                    {entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString('en-IN') : ''}
                  </span>
                </div>
                <div className={styles.auditAction}>
                  <span className={styles.actionTag}>{entry.action}</span>
                  {entry.decision && (
                    <span className={styles.decisionTag}>{entry.decision}</span>
                  )}
                </div>
                <p className={styles.auditJustification}>{entry.justification}</p>
                {entry.evidence_used?.length > 0 && (
                  <div className={styles.evidenceList}>
                    {entry.evidence_used.map((ev, j) => (
                      <span key={j} className={styles.evidenceChip}>{ev}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Replay tab */}
      {activeTab === 'replay' && (
        <div className={styles.formSection}>
          <h2 className={styles.formTitle}>Replay Exception</h2>
          <p className={styles.formDesc}>
            Re-run the exception resolution workflow with updated status information.
            This models the feedback loop where new payment status events arrive after the initial decision.
          </p>
          <form onSubmit={submitReplay} className={styles.form} aria-label="Replay form">
            <div className={styles.formField}>
              <label className={styles.formLabel}>New Status Event *</label>
              <input
                className={styles.formInput}
                value={replayForm.new_status_event}
                onChange={(e) => setReplayForm((f) => ({ ...f, new_status_event: e.target.value }))}
                placeholder="e.g. Network restored, retry succeeded"
                required
              />
            </div>
            <div className={styles.formField}>
              <label className={styles.formLabel}>Operator ID</label>
              <input
                className={styles.formInput}
                value={replayForm.operator_id}
                onChange={(e) => setReplayForm((f) => ({ ...f, operator_id: e.target.value }))}
                placeholder="OPS-001"
              />
            </div>
            <button
              className={styles.formBtn}
              type="submit"
              disabled={replayLoading || !replayForm.new_status_event}
              aria-busy={replayLoading}
            >
              {replayLoading ? <><span className={styles.spinner} aria-hidden="true" /> Processing...</> : '↩ Submit Replay'}
            </button>
          </form>
          {replayResult && (
            <div className={replayResult.error ? styles.resultError : styles.resultOk} aria-live="polite">
              {replayResult.error ? `Error: ${replayResult.error}` : (
                <>
                  <strong>Replay completed.</strong> New exception: <code>{replayResult.exception_id}</code>
                  {' · '}<StatusBadge status={replayResult.status} />
                  {' · '}<ActionBadge action={replayResult.resolution_action} />
                </>
              )}
            </div>
          )}
        </div>
      )}

      {/* Override tab */}
      {activeTab === 'override' && (
        <div className={styles.formSection}>
          <h2 className={styles.formTitle}>Operator Override</h2>
          <p className={styles.formDesc}>
            Manually override the agent's resolution decision. All overrides are permanently recorded in the audit trail.
          </p>
          <form onSubmit={submitOverride} className={styles.form} aria-label="Override form">
            <div className={styles.formField}>
              <label className={styles.formLabel}>Operator ID *</label>
              <input
                className={styles.formInput}
                value={overrideForm.operator_id}
                onChange={(e) => setOverrideForm((f) => ({ ...f, operator_id: e.target.value }))}
                placeholder="OPS-001"
                required
              />
            </div>
            <div className={styles.formField}>
              <label className={styles.formLabel}>Override Action *</label>
              <select
                className={styles.formInput}
                value={overrideForm.override_action}
                onChange={(e) => setOverrideForm((f) => ({ ...f, override_action: e.target.value }))}
                required
              >
                <option value="">Select action…</option>
                {['AUTO_RETRY','AUTO_CORRECT','CLIENT_OUTREACH','COMPLIANCE_REVIEW',
                  'HOLD_FOR_WINDOW','CANCEL','MANUAL_REVIEW','DUPLICATE_SUPPRESS'].map((a) => (
                  <option key={a} value={a}>{a}</option>
                ))}
              </select>
            </div>
            <div className={styles.formField}>
              <label className={styles.formLabel}>Justification *</label>
              <textarea
                className={styles.formTextarea}
                value={overrideForm.justification}
                onChange={(e) => setOverrideForm((f) => ({ ...f, justification: e.target.value }))}
                placeholder="Mandatory: explain why you are overriding the system's decision."
                required rows={4}
              />
            </div>
            <button
              className={`${styles.formBtn} ${styles.overrideBtn}`}
              type="submit"
              disabled={overrideLoading || !overrideForm.operator_id || !overrideForm.override_action || !overrideForm.justification}
              aria-busy={overrideLoading}
            >
              {overrideLoading ? <><span className={styles.spinner} aria-hidden="true" /> Applying...</> : '⚠ Apply Override'}
            </button>
          </form>
          {overrideResult && (
            <div className={overrideResult.error ? styles.resultError : styles.resultOk} aria-live="polite">
              {overrideResult.error ? `Error: ${overrideResult.error}` : '✓ Override applied and recorded in audit trail.'}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function InfoCard({ title, children, fullWidth }) {
  return (
    <div className={`${styles.infoCard} ${fullWidth ? styles.fullWidth : ''}`}>
      <h3 className={styles.infoCardTitle}>{title}</h3>
      <div className={styles.infoCardBody}>{children}</div>
    </div>
  )
}

function InfoRow({ label, children }) {
  return (
    <div className={styles.infoRow}>
      <span className={styles.infoLabel}>{label}</span>
      <span className={styles.infoValue}>{children}</span>
    </div>
  )
}
