import React, { useEffect, useState } from 'react'
import {
  AlertTriangle, CheckCircle, Clock, TrendingUp,
  ArrowRight, Activity, Shield, RefreshCw, Zap
} from 'lucide-react'
import { api } from '../api.js'
import { StatusBadge, FailureBadge, ActionBadge } from './StatusBadge.jsx'
import styles from './Dashboard.module.css'

const SAMPLE_SCENARIOS = [
  {
    label: 'Insufficient Funds',
    payment_id: `PAY-${Date.now()}-001`,
    client_id: 'CLT-4521',
    account_id: 'ACC-10023456',
    payment_rail: 'NEFT',
    payment_type: 'domestic_transfer',
    amount: 75000,
    currency: 'INR',
    beneficiary_details: { account_no: '123456789012', ifsc: 'HDFC0001234', name: 'Rajesh Kumar' },
    failure_code: 'INSUF_FUNDS',
    failure_message: 'Available balance insufficient for debit',
    triggered_by: 'system_event',
  },
  {
    label: 'Invalid IFSC Code',
    payment_id: `PAY-${Date.now()}-002`,
    client_id: 'CLT-7830',
    account_id: 'ACC-20045678',
    payment_rail: 'NEFT',
    payment_type: 'domestic_transfer',
    amount: 12500,
    currency: 'INR',
    beneficiary_details: { account_no: '987654321098', ifsc: 'INVALIDIFSC', name: 'Priya Sharma' },
    failure_code: 'INVALID_IFSC',
    failure_message: 'IFSC code not found in RBI directory',
    triggered_by: 'system_event',
  },
  {
    label: 'AML Compliance Hold',
    payment_id: `PAY-${Date.now()}-003`,
    client_id: 'CLT-3341',
    account_id: 'ACC-30067890',
    payment_rail: 'SWIFT',
    payment_type: 'wire',
    amount: 150000,
    currency: 'USD',
    beneficiary_details: { iban: 'DE89370400440532013000', bic: 'COBADEFFXXX', name: 'International Corp Ltd' },
    failure_code: 'AML_HOLD',
    failure_message: 'Transaction flagged by AML screening',
    triggered_by: 'system_event',
  },
  {
    label: 'Network / Rail Outage',
    payment_id: `PAY-${Date.now()}-004`,
    client_id: 'CLT-9102',
    account_id: 'ACC-40089012',
    payment_rail: 'RTGS',
    payment_type: 'domestic_transfer',
    amount: 500000,
    currency: 'INR',
    beneficiary_details: { account_no: '112233445566', ifsc: 'SBIN0001234', name: 'Ananya Enterprises' },
    failure_code: 'NETWORK_ERROR',
    failure_message: 'RTGS clearing network unreachable',
    triggered_by: 'system_event',
  },
  {
    label: 'Duplicate Payment',
    payment_id: `PAY-${Date.now()}-005`,
    client_id: 'CLT-6654',
    account_id: 'ACC-50091234',
    payment_rail: 'UPI',
    payment_type: 'domestic_transfer',
    amount: 5000,
    currency: 'INR',
    beneficiary_details: { upi_id: 'merchant@okicici', name: 'Metro Retail Pvt Ltd' },
    failure_code: 'DUPLICATE_TXN',
    failure_message: 'Duplicate transaction detected within 5-minute window',
    triggered_by: 'system_event',
  },
]

function StatCard({ icon: Icon, label, value, color, sub }) {
  return (
    <div className={styles.statCard}>
      <div className={styles.statIcon} style={{ background: color + '18', color }}>
        <Icon size={22} aria-hidden="true" />
      </div>
      <div className={styles.statBody}>
        <span className={styles.statValue}>{value}</span>
        <span className={styles.statLabel}>{label}</span>
        {sub && <span className={styles.statSub}>{sub}</span>}
      </div>
    </div>
  )
}

export default function Dashboard({ navigate, VIEWS }) {
  const [metrics, setMetrics]     = useState(null)
  const [recent, setRecent]       = useState([])
  const [loading, setLoading]     = useState(true)
  const [demoLoading, setDemoLoading] = useState(null)
  const [demoResult, setDemoResult]   = useState(null)
  const [error, setError]         = useState(null)

  const loadData = async () => {
    setLoading(true)
    try {
      const [m, r] = await Promise.all([
        api.getMetrics(),
        api.listExceptions({ limit: 5 }),
      ])
      setMetrics(m)
      setRecent(r)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  const runDemo = async (scenario) => {
    setDemoLoading(scenario.label)
    setDemoResult(null)
    try {
      const payload = { ...scenario, payment_id: `PAY-${Date.now()}-DEMO` }
      const result = await api.submitException(payload)
      setDemoResult(result)
      loadData()
    } catch (e) {
      setDemoResult({ error: e.message })
    } finally {
      setDemoLoading(null)
    }
  }

  return (
    <div className={styles.root}>
      {/* Page header */}
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Operations Dashboard</h1>
          <p className={styles.subtitle}>
            Real-time overview of payment exception resolution activity
          </p>
        </div>
        <button className={styles.refreshBtn} onClick={loadData} aria-label="Refresh dashboard">
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {error && (
        <div className={styles.errorBanner} role="alert">
          <AlertTriangle size={16} />
          {error}. Make sure the backend is running on port 8000.
        </div>
      )}

      {/* KPI Stats */}
      <section className={styles.statsGrid} aria-label="Key metrics">
        <StatCard
          icon={Activity}
          label="Total Exceptions"
          value={loading ? '—' : metrics?.total_exceptions ?? 0}
          color="#2563eb"
          sub="Since last restart"
        />
        <StatCard
          icon={Zap}
          label="Auto-Resolved"
          value={loading ? '—' : `${metrics?.automation_rate_pct ?? 0}%`}
          color="#16a34a"
          sub={`${metrics?.auto_resolved ?? 0} cases`}
        />
        <StatCard
          icon={Shield}
          label="Escalated"
          value={loading ? '—' : metrics?.escalated_exceptions ?? 0}
          color="#dc2626"
          sub={`${metrics?.escalation_rate_pct ?? 0}% rate`}
        />
        <StatCard
          icon={Clock}
          label="Avg Resolution Time"
          value={loading ? '—' : `${metrics?.average_response_time_s ?? 0}s`}
          color="#d97706"
          sub="End-to-end"
        />
      </section>

      {/* Two-column layout */}
      <div className={styles.twoCol}>

        {/* Quick Demo Scenarios */}
        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>
              <TrendingUp size={18} aria-hidden="true" />
              Quick Demo Scenarios
            </h2>
            <span className={styles.cardHint}>Click to trigger live resolution</span>
          </div>
          <div className={styles.scenarioList}>
            {SAMPLE_SCENARIOS.map((s) => (
              <button
                key={s.label}
                className={styles.scenarioBtn}
                onClick={() => runDemo(s)}
                disabled={!!demoLoading}
                aria-busy={demoLoading === s.label}
              >
                <span className={styles.scenarioLabel}>{s.label}</span>
                <span className={styles.scenarioMeta}>
                  {s.payment_rail} · ₹{s.amount.toLocaleString()} · {s.currency}
                </span>
                {demoLoading === s.label ? (
                  <span className={styles.spinner} aria-hidden="true" />
                ) : (
                  <ArrowRight size={14} aria-hidden="true" />
                )}
              </button>
            ))}
          </div>
          {demoResult && (
            <div className={styles.demoResult} aria-live="polite">
              {demoResult.error ? (
                <p className={styles.demoError}>Error: {demoResult.error}</p>
              ) : (
                <div className={styles.demoSuccess}>
                  <div className={styles.demoRow}>
                    <span>Exception ID</span>
                    <strong>{demoResult.exception_id}</strong>
                  </div>
                  <div className={styles.demoRow}>
                    <span>Failure Type</span>
                    <FailureBadge type={demoResult.failure_type} />
                  </div>
                  <div className={styles.demoRow}>
                    <span>Resolution</span>
                    <ActionBadge action={demoResult.resolution_action} />
                  </div>
                  <div className={styles.demoRow}>
                    <span>Status</span>
                    <StatusBadge status={demoResult.status} />
                  </div>
                  <div className={styles.demoRow}>
                    <span>Processing Time</span>
                    <strong>{demoResult.processing_time_s}s</strong>
                  </div>
                  <button
                    className={styles.viewDetailBtn}
                    onClick={() => navigate(VIEWS.DETAIL, demoResult.exception_id)}
                  >
                    View Full Details →
                  </button>
                </div>
              )}
            </div>
          )}
        </section>

        {/* Recent Exceptions */}
        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <h2 className={styles.cardTitle}>
              <CheckCircle size={18} aria-hidden="true" />
              Recent Exceptions
            </h2>
            <button
              className={styles.viewAllBtn}
              onClick={() => navigate(VIEWS.LIST)}
            >
              View All →
            </button>
          </div>
          {recent.length === 0 && !loading && (
            <p className={styles.empty}>
              No exceptions yet. Run a demo scenario or submit one manually.
            </p>
          )}
          <ul className={styles.recentList} role="list">
            {recent.map((exc) => (
              <li
                key={exc.exception_id}
                className={styles.recentItem}
                onClick={() => navigate(VIEWS.DETAIL, exc.exception_id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && navigate(VIEWS.DETAIL, exc.exception_id)}
                aria-label={`Exception ${exc.exception_id}`}
              >
                <div className={styles.recentLeft}>
                  <span className={styles.recentId}>{exc.exception_id}</span>
                  <FailureBadge type={exc.failure_type} />
                </div>
                <div className={styles.recentRight}>
                  <StatusBadge status={exc.status} />
                  <ActionBadge action={exc.resolution_action} />
                </div>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  )
}
