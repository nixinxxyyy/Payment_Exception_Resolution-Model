import React, { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import { RefreshCw } from 'lucide-react'
import { api } from '../api.js'
import styles from './MetricsPanel.module.css'

const COLORS = ['#163468','#c9a227','#16a34a','#dc2626','#7c3aed','#0891b2','#d97706']

function StatBox({ label, value, sub, color }) {
  return (
    <div className={styles.statBox} style={{ borderLeftColor: color }}>
      <span className={styles.statVal} style={{ color }}>{value}</span>
      <span className={styles.statLbl}>{label}</span>
      {sub && <span className={styles.statSub}>{sub}</span>}
    </div>
  )
}

export default function MetricsPanel() {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  const load = async () => {
    setLoading(true)
    try {
      const m = await api.getMetrics()
      setData(m)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const failureChartData = data
    ? Object.entries(data.failure_type_distribution || {}).map(([k, v]) => ({
        name: k.replace(/_/g, ' '),
        count: v,
      }))
    : []

  const resolutionChartData = data
    ? Object.entries(data.resolution_distribution || {}).map(([k, v]) => ({
        name: k.replace(/_/g, ' '),
        value: v,
      }))
    : []

  return (
    <div className={styles.root}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Analytics</h1>
          <p className={styles.subtitle}>System performance metrics since last restart</p>
        </div>
        <button className={styles.refreshBtn} onClick={load} aria-label="Refresh metrics">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {error && <div className={styles.error} role="alert">{error}</div>}

      {loading && <div className={styles.loading} aria-busy="true"><span className={styles.spinner} aria-hidden="true" /> Loading...</div>}

      {!loading && data && (
        <>
          {/* KPI row */}
          <div className={styles.kpiRow} aria-label="Key performance indicators">
            <StatBox label="Total Exceptions"    value={data.total_exceptions}    color="#163468" />
            <StatBox label="Auto-Resolved"        value={data.auto_resolved}       color="#16a34a" sub={`${data.automation_rate_pct}%`} />
            <StatBox label="Escalated"            value={data.escalated_exceptions} color="#dc2626" sub={`${data.escalation_rate_pct}%`} />
            <StatBox label="Avg Resolution"       value={`${data.average_response_time_s}s`} color="#d97706" />
            <StatBox label="Min Resolution"       value={`${data.min_response_time_s || 0}s`}  color="#0891b2" />
            <StatBox label="Max Resolution"       value={`${data.max_response_time_s || 0}s`}  color="#7c3aed" />
          </div>

          {/* Charts */}
          <div className={styles.charts}>
            <div className={styles.chartCard}>
              <h2 className={styles.chartTitle}>Failure Type Distribution</h2>
              {failureChartData.length === 0 ? (
                <p className={styles.noData}>No data yet. Submit some exceptions first.</p>
              ) : (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={failureChartData} margin={{ left: 0, right: 20, top: 10, bottom: 60 }}>
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} angle={-35} textAnchor="end" />
                    <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                    <Tooltip contentStyle={{ fontSize: 13 }} />
                    <Bar dataKey="count" fill="#163468" radius={[4, 4, 0, 0]}>
                      {failureChartData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            <div className={styles.chartCard}>
              <h2 className={styles.chartTitle}>Resolution Action Distribution</h2>
              {resolutionChartData.length === 0 ? (
                <p className={styles.noData}>No data yet.</p>
              ) : (
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie
                      data={resolutionChartData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%" cy="45%"
                      outerRadius={90}
                      label={({ name, percent }) =>
                        `${name.split(' ')[0]} (${(percent * 100).toFixed(0)}%)`
                      }
                      labelLine={false}
                    >
                      {resolutionChartData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ fontSize: 13 }} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Raw tables */}
          <div className={styles.tableRow}>
            <MetricTable
              title="By Failure Type"
              rows={data.failure_type_distribution}
              total={data.total_exceptions}
            />
            <MetricTable
              title="By Resolution Action"
              rows={data.resolution_distribution}
              total={data.total_exceptions}
            />
          </div>
        </>
      )}
    </div>
  )
}

function MetricTable({ title, rows, total }) {
  return (
    <div className={styles.metricTable}>
      <h3 className={styles.tableTitle}>{title}</h3>
      <table className={styles.table} aria-label={title}>
        <thead>
          <tr>
            <th scope="col">Category</th>
            <th scope="col">Count</th>
            <th scope="col">Share</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(rows || {}).length === 0 ? (
            <tr><td colSpan={3} className={styles.empty}>No data</td></tr>
          ) : (
            Object.entries(rows || {}).sort(([,a], [,b]) => b - a).map(([k, v]) => (
              <tr key={k}>
                <td>{k.replace(/_/g, ' ')}</td>
                <td className={styles.numCell}>{v}</td>
                <td className={styles.numCell}>{total > 0 ? `${((v / total) * 100).toFixed(1)}%` : '—'}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
