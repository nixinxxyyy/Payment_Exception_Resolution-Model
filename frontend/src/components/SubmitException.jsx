import React, { useState, useRef, useEffect } from 'react'
import { AlertCircle, CheckCircle2, Send, Zap, ChevronDown } from 'lucide-react'
import { api } from '../api.js'
import { StatusBadge, FailureBadge, ActionBadge } from './StatusBadge.jsx'
import AgentPipeline from './AgentPipeline.jsx'
import styles from './SubmitException.module.css'

const RAILS = ['NEFT', 'RTGS', 'IMPS', 'SWIFT', 'UPI', 'INTERNAL']
const TYPES = ['domestic_transfer', 'wire', 'book_transfer', 'disbursement']
const CODES = [
  'INSUF_FUNDS', 'BALANCE_LOW', 'INVALID_ACCOUNT', 'INVALID_IFSC',
  'INVALID_UPI', 'BENEFICIARY_MISMATCH', 'DUPLICATE_TXN',
  'AML_HOLD', 'SANCTIONS_HOLD', 'COMPLIANCE_BLOCK',
  'NETWORK_ERROR', 'CLEARING_TIMEOUT', 'RAIL_UNAVAILABLE',
  'CUTOFF_EXCEEDED', 'RETRY_PENDING', 'RETRY_UNKNOWN',
]

// ── Pre-filled demo scenarios ──────────────────────────────────────────────
const DEMO_SCENARIOS = [
  {
    label: '💸 Insufficient Funds — NEFT transfer',
    form: {
      payment_id: 'PAY-20260609-INF01', client_id: 'CLT-4521',
      account_id: 'ACC-10023456', payment_rail: 'NEFT',
      payment_type: 'domestic_transfer', amount: '75000', currency: 'INR',
      failure_code: 'INSUF_FUNDS',
      failure_message: 'Available balance ₹42,310 is insufficient for debit of ₹75,000',
      triggered_by: 'system_event',
      account_no: '123456789012', ifsc: 'HDFC0001234', ben_name: 'Rajesh Kumar',
      iban: '', bic: '', upi_id: '',
    },
  },
  {
    label: '🏦 Invalid IFSC Code — Beneficiary error',
    form: {
      payment_id: 'PAY-20260609-IFC02', client_id: 'CLT-7830',
      account_id: 'ACC-20045678', payment_rail: 'NEFT',
      payment_type: 'domestic_transfer', amount: '12500', currency: 'INR',
      failure_code: 'INVALID_IFSC',
      failure_message: 'IFSC INVALIFSC9 not found in RBI NEFT directory',
      triggered_by: 'system_event',
      account_no: '987654321098', ifsc: 'INVALIFSC9', ben_name: 'Priya Sharma',
      iban: '', bic: '', upi_id: '',
    },
  },
  {
    label: '🛡️ AML Compliance Hold — SWIFT wire',
    form: {
      payment_id: 'PAY-20260609-AML03', client_id: 'CLT-3341',
      account_id: 'ACC-30067890', payment_rail: 'SWIFT',
      payment_type: 'wire', amount: '150000', currency: 'USD',
      failure_code: 'AML_HOLD',
      failure_message: 'Transaction flagged by AML screening engine — high-value cross-border',
      triggered_by: 'system_event',
      account_no: '', ifsc: '', iban: 'DE89370400440532013000',
      bic: 'COBADEFFXXX', ben_name: 'International Corp Ltd', upi_id: '',
    },
  },
  {
    label: '📡 Network / Rail Outage — RTGS failure',
    form: {
      payment_id: 'PAY-20260609-NET04', client_id: 'CLT-9102',
      account_id: 'ACC-40089012', payment_rail: 'RTGS',
      payment_type: 'domestic_transfer', amount: '500000', currency: 'INR',
      failure_code: 'NETWORK_ERROR',
      failure_message: 'RTGS clearing network unreachable — gateway timeout after 30s',
      triggered_by: 'system_event',
      account_no: '112233445566', ifsc: 'SBIN0001234', ben_name: 'Ananya Enterprises',
      iban: '', bic: '', upi_id: '',
    },
  },
  {
    label: '🔁 Duplicate Payment — UPI double-tap',
    form: {
      payment_id: 'PAY-20260609-DUP05', client_id: 'CLT-6654',
      account_id: 'ACC-50091234', payment_rail: 'UPI',
      payment_type: 'domestic_transfer', amount: '5000', currency: 'INR',
      failure_code: 'DUPLICATE_TXN',
      failure_message: 'Duplicate transaction detected within 5-minute deduplication window',
      triggered_by: 'system_event',
      account_no: '', ifsc: '', iban: '', bic: '',
      upi_id: 'merchant@okicici', ben_name: 'Metro Retail Pvt Ltd',
    },
  },
  {
    label: '⏰ Cut-off Missed — RTGS after 17:00',
    form: {
      payment_id: 'PAY-20260609-CUT06', client_id: 'CLT-2211',
      account_id: 'ACC-60012345', payment_rail: 'RTGS',
      payment_type: 'domestic_transfer', amount: '200000', currency: 'INR',
      failure_code: 'CUTOFF_EXCEEDED',
      failure_message: 'Payment submitted at 17:42 UTC — after RTGS daily cut-off of 17:00',
      triggered_by: 'system_event',
      account_no: '998877665544', ifsc: 'ICIC0001234', ben_name: 'Sunrise Industries',
      iban: '', bic: '', upi_id: '',
    },
  },
  {
    label: '❓ Uncertain Retry Status — prior retry unknown',
    form: {
      payment_id: 'PAY-20260609-URS07', client_id: 'CLT-8876',
      account_id: 'ACC-70067890', payment_rail: 'NEFT',
      payment_type: 'domestic_transfer', amount: '35000', currency: 'INR',
      failure_code: 'RETRY_UNKNOWN',
      failure_message: 'Prior retry at 14:22 UTC has unknown status — debit state uncertain',
      triggered_by: 'system_event',
      account_no: '445566778899', ifsc: 'AXIS0001234', ben_name: 'Tech Solutions Ltd',
      iban: '', bic: '', upi_id: '',
    },
  },
]

const BLANK = {
  payment_id: '', client_id: '', account_id: '', payment_rail: 'NEFT',
  payment_type: 'domestic_transfer', amount: '', currency: 'INR',
  failure_code: 'INVALID_IFSC', failure_message: '', triggered_by: 'system_event',
  account_no: '', ifsc: '', iban: '', bic: '', upi_id: '', ben_name: '',
}

function Field({ label, children, required, hint }) {
  return (
    <div className={styles.field}>
      <label className={styles.label}>
        {label}
        {required && <span className={styles.req} aria-hidden="true"> *</span>}
        {hint && <span className={styles.hint}>{hint}</span>}
      </label>
      {children}
    </div>
  )
}

export default function SubmitException({ navigate, VIEWS }) {
  const [form, setForm]         = useState(DEMO_SCENARIOS[0].form)
  const [loading, setLoading]   = useState(false)
  const [result, setResult]     = useState(null)
  const [error, setError]       = useState(null)
  const [showScenarios, setShowScenarios] = useState(false)

  // Real-time pipeline state
  const [pipelineActive, setPipelineActive] = useState(false)
  const [pipelineEvents, setPipelineEvents] = useState([])
  const [pipelineDone, setPipelineDone]     = useState(false)
  const [currentException, setCurrentException] = useState(null)
  const esRef = useRef(null)

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const loadScenario = (s) => {
    setForm(s.form)
    setShowScenarios(false)
    setResult(null)
    setError(null)
    resetPipeline()
  }

  const resetPipeline = () => {
    if (esRef.current) { esRef.current.close(); esRef.current = null }
    setPipelineActive(false)
    setPipelineEvents([])
    setPipelineDone(false)
    setCurrentException(null)
  }

  // Cleanup SSE on unmount
  useEffect(() => () => { if (esRef.current) esRef.current.close() }, [])

  const requiredFields = ['payment_id', 'client_id', 'account_id', 'amount', 'failure_code']
  const valid = requiredFields.every((f) => String(form[f]).trim())

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)
    resetPipeline()

    const payload = {
      payment_id:      form.payment_id,
      client_id:       form.client_id,
      account_id:      form.account_id,
      payment_rail:    form.payment_rail,
      payment_type:    form.payment_type,
      amount:          parseFloat(form.amount),
      currency:        form.currency,
      failure_code:    form.failure_code,
      failure_message: form.failure_message,
      triggered_by:    form.triggered_by,
      beneficiary_details: {
        account_no: form.account_no || undefined,
        ifsc:       form.ifsc       || undefined,
        iban:       form.iban       || undefined,
        bic:        form.bic        || undefined,
        upi_id:     form.upi_id     || undefined,
        name:       form.ben_name   || undefined,
      },
    }

    try {
      // Use streaming submit endpoint
      const init = await fetch(`${import.meta.env.VITE_API_BASE_URL || ''}/api/v1/exceptions/submit-stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!init.ok) {
        const err = await init.json()
        throw new Error(err.detail || 'Submission failed')
      }
      const { exception_id, stream_url } = await init.json()
      setCurrentException(exception_id)
      setPipelineActive(true)
      setLoading(false)

      // Connect SSE — use api.streamUrl() so it works on Vercel too
      const es = new EventSource(api.streamUrl(exception_id))
      esRef.current = es

      es.addEventListener('agent_complete', (ev) => {
        const data = JSON.parse(ev.data)
        setPipelineEvents((prev) => [...prev, { type: 'agent_complete', ...data }])
      })

      es.addEventListener('pipeline_done', (ev) => {
        const data = JSON.parse(ev.data)
        setPipelineDone(true)
        setResult({
          exception_id:        data.exception_id,
          payment_id:          payload.payment_id,
          failure_type:        data.failure_type,
          resolution_action:   data.resolution_action,
          status:              data.status,
          decision_confidence: data.decision_confidence,
          decision_rationale:  data.decision_rationale,
          escalation_queue:    data.escalation_queue,
          client_message:      data.client_message,
          retry_count:         data.retry_count,
          audit_trail_length:  data.audit_trail_length,
          processing_time_s:   '—',
        })
        es.close()
      })

      es.addEventListener('pipeline_error', (ev) => {
        const data = JSON.parse(ev.data)
        setError(data.error)
        setPipelineDone(true)
        es.close()
      })

      es.addEventListener('done', () => { es.close() })
      es.onerror = () => {
        setError('Connection lost — check backend is running.')
        es.close()
        setLoading(false)
      }

    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  const showBeneficiaryField = (field) => {
    if (field === 'upi_id') return form.payment_rail === 'UPI'
    if (field === 'iban' || field === 'bic') return form.payment_rail === 'SWIFT'
    return ['NEFT', 'RTGS', 'IMPS', 'INTERNAL'].includes(form.payment_rail)
  }

  return (
    <div className={styles.root}>
      {/* Header */}
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Submit Payment Exception</h1>
          <p className={styles.subtitle}>
            Trigger the multi-agent resolution workflow for a failed payment transaction.
          </p>
        </div>
        {/* Scenario picker */}
        <div className={styles.scenarioPicker}>
          <button
            className={styles.scenarioToggle}
            onClick={() => setShowScenarios((v) => !v)}
            type="button"
            aria-expanded={showScenarios}
            aria-haspopup="listbox"
          >
            <Zap size={14} aria-hidden="true" />
            Load Demo Scenario
            <ChevronDown size={13} style={{ transform: showScenarios ? 'rotate(180deg)' : 'none', transition: '0.2s' }} />
          </button>
          {showScenarios && (
            <ul className={styles.scenarioDropdown} role="listbox" aria-label="Demo scenarios">
              {DEMO_SCENARIOS.map((s) => (
                <li key={s.label}>
                  <button
                    className={styles.scenarioOption}
                    onClick={() => loadScenario(s)}
                    role="option"
                    type="button"
                  >
                    {s.label}
                  </button>
                </li>
              ))}
              <li>
                <button
                  className={`${styles.scenarioOption} ${styles.blankOption}`}
                  onClick={() => { setForm(BLANK); setShowScenarios(false); resetPipeline() }}
                  role="option"
                  type="button"
                >
                  ✏️ Start with blank form
                </button>
              </li>
            </ul>
          )}
        </div>
      </div>

      <div className={styles.layout}>
        {/* Form */}
        <form className={styles.form} onSubmit={submit} noValidate aria-label="Payment exception submission form">

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Payment Details</h2>
            <div className={styles.grid2}>
              <Field label="Payment ID" required>
                <input className={styles.input} value={form.payment_id} onChange={set('payment_id')} placeholder="PAY-20260601-001" required />
              </Field>
              <Field label="Client ID" required>
                <input className={styles.input} value={form.client_id} onChange={set('client_id')} placeholder="CLT-4521" required />
              </Field>
              <Field label="Account ID" required>
                <input className={styles.input} value={form.account_id} onChange={set('account_id')} placeholder="ACC-10023456" required />
              </Field>
              <Field label="Amount" required>
                <input className={styles.input} type="number" value={form.amount} onChange={set('amount')} placeholder="25000" min="0.01" step="0.01" required />
              </Field>
              <Field label="Currency">
                <select className={styles.select} value={form.currency} onChange={set('currency')}>
                  <option>INR</option><option>USD</option><option>EUR</option><option>GBP</option>
                </select>
              </Field>
              <Field label="Payment Rail">
                <select className={styles.select} value={form.payment_rail} onChange={set('payment_rail')}>
                  {RAILS.map((r) => <option key={r}>{r}</option>)}
                </select>
              </Field>
              <Field label="Payment Type">
                <select className={styles.select} value={form.payment_type} onChange={set('payment_type')}>
                  {TYPES.map((t) => <option key={t}>{t}</option>)}
                </select>
              </Field>
              <Field label="Triggered By">
                <select className={styles.select} value={form.triggered_by} onChange={set('triggered_by')}>
                  <option value="system_event">System Event</option>
                  <option value="manual">Manual</option>
                  <option value="replay">Replay</option>
                </select>
              </Field>
            </div>
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Failure Information</h2>
            <div className={styles.grid2}>
              <Field label="Failure Code" required>
                <select className={styles.select} value={form.failure_code} onChange={set('failure_code')}>
                  {CODES.map((c) => <option key={c}>{c}</option>)}
                </select>
              </Field>
              <Field label="Failure Message" hint="(optional)">
                <input className={styles.input} value={form.failure_message} onChange={set('failure_message')} placeholder="Human-readable error from payment system" />
              </Field>
            </div>
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Beneficiary Details</h2>
            <div className={styles.grid2}>
              <Field label="Beneficiary Name" hint="(optional)">
                <input className={styles.input} value={form.ben_name} onChange={set('ben_name')} placeholder="Full legal name" />
              </Field>
              {showBeneficiaryField('account_no') && (
                <Field label="Account Number">
                  <input className={styles.input} value={form.account_no} onChange={set('account_no')} placeholder="123456789012" />
                </Field>
              )}
              {showBeneficiaryField('ifsc') && (
                <Field label="IFSC Code">
                  <input className={styles.input} value={form.ifsc} onChange={set('ifsc')} placeholder="HDFC0001234" />
                </Field>
              )}
              {showBeneficiaryField('iban') && (
                <Field label="IBAN">
                  <input className={styles.input} value={form.iban} onChange={set('iban')} placeholder="DE89370400440532013000" />
                </Field>
              )}
              {showBeneficiaryField('bic') && (
                <Field label="BIC / SWIFT Code">
                  <input className={styles.input} value={form.bic} onChange={set('bic')} placeholder="COBADEFFXXX" />
                </Field>
              )}
              {showBeneficiaryField('upi_id') && (
                <Field label="UPI ID">
                  <input className={styles.input} value={form.upi_id} onChange={set('upi_id')} placeholder="merchant@okicici" />
                </Field>
              )}
            </div>
          </section>

          <button
            type="submit"
            className={styles.submitBtn}
            disabled={!valid || loading || pipelineActive}
            aria-busy={loading || pipelineActive}
          >
            {loading ? (
              <><span className={styles.spinner} aria-hidden="true" /> Initialising...</>
            ) : pipelineActive && !pipelineDone ? (
              <><span className={styles.spinner} aria-hidden="true" /> Agents running...</>
            ) : (
              <><Send size={16} aria-hidden="true" /> Submit Exception</>
            )}
          </button>
        </form>

        {/* Right column: pipeline + result */}
        <div className={styles.rightCol}>
          {/* Agent pipeline visualiser */}
          {(pipelineActive || pipelineEvents.length > 0) && (
            <AgentPipeline
              events={pipelineEvents}
              done={pipelineDone}
              exceptionId={currentException}
            />
          )}

          {/* Error */}
          {error && (
            <div className={styles.errorResult} role="alert">
              <AlertCircle size={18} />
              <div>
                <strong>Failed</strong>
                <p>{error}</p>
              </div>
            </div>
          )}

          {/* Final result card */}
          {result && pipelineDone && (
            <aside className={styles.resultPanel} aria-live="polite" aria-label="Resolution result">
              <div className={styles.successResult}>
                <div className={styles.resultHeader}>
                  <CheckCircle2 size={18} color="var(--status-resolved)" />
                  <strong>Resolution Complete</strong>
                </div>
                <div className={styles.resultGrid}>
                  <ResultRow label="Exception ID">
                    <code className={styles.code}>{result.exception_id}</code>
                  </ResultRow>
                  <ResultRow label="Status"><StatusBadge status={result.status} /></ResultRow>
                  <ResultRow label="Failure Type"><FailureBadge type={result.failure_type} /></ResultRow>
                  <ResultRow label="Resolution"><ActionBadge action={result.resolution_action} /></ResultRow>
                  <ResultRow label="Confidence">
                    <span className={styles.conf}>{Math.round((result.decision_confidence || 0) * 100)}%</span>
                  </ResultRow>
                  <ResultRow label="Retries">{result.retry_count}</ResultRow>
                  <ResultRow label="Audit Entries">{result.audit_trail_length}</ResultRow>
                </div>
                {result.escalation_queue && (
                  <div className={styles.queueNote}>
                    🏦 Escalated to: <strong>{result.escalation_queue}</strong>
                  </div>
                )}
                {result.decision_rationale && (
                  <div className={styles.rationale}>
                    <strong>Decision Rationale</strong>
                    <p>{result.decision_rationale}</p>
                  </div>
                )}
                {result.client_message && (
                  <div className={styles.clientMsg}>
                    <strong>Client Communication</strong>
                    <pre className={styles.msgPre}>{result.client_message}</pre>
                  </div>
                )}
                <button
                  className={styles.detailBtn}
                  onClick={() => navigate(VIEWS.DETAIL, result.exception_id)}
                >
                  View Full Audit Trail →
                </button>
              </div>
            </aside>
          )}
        </div>
      </div>
    </div>
  )
}

function ResultRow({ label, children }) {
  return (
    <div className={styles.resultRow}>
      <span className={styles.resultLabel}>{label}</span>
      <span className={styles.resultValue}>{children}</span>
    </div>
  )
}
