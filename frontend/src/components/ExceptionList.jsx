import React, { useEffect, useState } from 'react'
import { Search, Filter, RefreshCw, ChevronRight } from 'lucide-react'
import { api } from '../api.js'
import { StatusBadge, FailureBadge, ActionBadge } from './StatusBadge.jsx'
import styles from './ExceptionList.module.css'

const STATUSES      = ['', 'INGESTED', 'INVESTIGATING', 'DECIDED', 'EXECUTING', 'AWAITING_INPUT', 'RESOLVED', 'ESCALATED', 'HELD', 'CANCELLED']
const FAILURE_TYPES = ['', 'INCORRECT_BENEFICIARY', 'INSUFFICIENT_FUNDS', 'DUPLICATE_PAYMENT', 'COMPLIANCE_HOLD', 'NETWORK_RAIL_FAILURE', 'CUTOFF_TIME_MISS', 'UNCERTAIN_RETRY_STATUS', 'UNKNOWN']
const RAILS         = ['', 'NEFT', 'RTGS', 'IMPS', 'SWIFT', 'UPI', 'INTERNAL']

export default function ExceptionList({ onSelect }) {
  const [items,        setItems]        = useState([])
  const [loading,      setLoading]      = useState(true)
  const [error,        setError]        = useState(null)
  const [filters,      setFilters]      = useState({ status: '', failure_type: '', payment_rail: '' })
  const [searchText,   setSearchText]   = useState('')

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = {}
      if (filters.status)       params.status       = filters.status
      if (filters.failure_type) params.failure_type = filters.failure_type
      if (filters.payment_rail) params.payment_rail = filters.payment_rail
      const data = await api.listExceptions({ ...params, limit: 100 })
      setItems(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [filters])

  const setFilter = (k) => (e) => setFilters((f) => ({ ...f, [k]: e.target.value }))

  const filtered = searchText
    ? items.filter((i) =>
        i.exception_id.toLowerCase().includes(searchText.toLowerCase()) ||
        i.payment_id.toLowerCase().includes(searchText.toLowerCase())
      )
    : items

  return (
    <div className={styles.root}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Payment Exceptions</h1>
          <p className={styles.subtitle}>{filtered.length} exception{filtered.length !== 1 ? 's' : ''} found</p>
        </div>
        <button className={styles.refreshBtn} onClick={load} aria-label="Refresh list">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Filters */}
      <div className={styles.filterBar} role="search" aria-label="Filter exceptions">
        <div className={styles.searchWrap}>
          <Search size={14} className={styles.searchIcon} aria-hidden="true" />
          <input
            className={styles.searchInput}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="Search by exception ID or payment ID…"
            aria-label="Search exceptions"
          />
        </div>
        <div className={styles.filters}>
          <Filter size={14} aria-hidden="true" />
          <select className={styles.filterSelect} value={filters.status} onChange={setFilter('status')} aria-label="Filter by status">
            {STATUSES.map((s) => <option key={s} value={s}>{s || 'All Statuses'}</option>)}
          </select>
          <select className={styles.filterSelect} value={filters.failure_type} onChange={setFilter('failure_type')} aria-label="Filter by failure type">
            {FAILURE_TYPES.map((t) => <option key={t} value={t}>{t || 'All Failure Types'}</option>)}
          </select>
          <select className={styles.filterSelect} value={filters.payment_rail} onChange={setFilter('payment_rail')} aria-label="Filter by payment rail">
            {RAILS.map((r) => <option key={r} value={r}>{r || 'All Rails'}</option>)}
          </select>
        </div>
      </div>

      {error && (
        <div className={styles.error} role="alert">Error: {error}</div>
      )}

      {/* Table */}
      <div className={styles.tableWrap}>
        <table className={styles.table} role="grid" aria-label="Payment exceptions table">
          <thead>
            <tr>
              <th scope="col">Exception ID</th>
              <th scope="col">Payment ID</th>
              <th scope="col">Status</th>
              <th scope="col">Failure Type</th>
              <th scope="col">Resolution</th>
              <th scope="col">Retries</th>
              <th scope="col">Submitted</th>
              <th scope="col"><span className={styles.srOnly}>Actions</span></th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={8} className={styles.loadingRow}>
                  <span className={styles.spinner} aria-hidden="true" />
                  Loading exceptions...
                </td>
              </tr>
            )}
            {!loading && filtered.length === 0 && (
              <tr>
                <td colSpan={8} className={styles.emptyRow}>
                  No exceptions match the current filters.
                </td>
              </tr>
            )}
            {!loading && filtered.map((exc) => (
              <tr
                key={exc.exception_id}
                className={styles.row}
                onClick={() => onSelect(exc.exception_id)}
                role="row"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && onSelect(exc.exception_id)}
                aria-label={`Exception ${exc.exception_id}`}
              >
                <td><code className={styles.idCode}>{exc.exception_id}</code></td>
                <td><code className={styles.idCode}>{exc.payment_id}</code></td>
                <td><StatusBadge status={exc.status} /></td>
                <td><FailureBadge type={exc.failure_type} /></td>
                <td><ActionBadge action={exc.resolution_action} /></td>
                <td className={styles.center}>{exc.retry_count}</td>
                <td className={styles.date}>
                  {exc.submitted_at
                    ? new Date(exc.submitted_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
                    : '—'}
                </td>
                <td>
                  <ChevronRight size={16} className={styles.chevron} aria-hidden="true" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
