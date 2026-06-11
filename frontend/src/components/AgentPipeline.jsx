import React, { useEffect, useRef } from 'react'
import styles from './AgentPipeline.module.css'

// All 9 agents in workflow order
const ALL_AGENTS = [
  { key: 'ingestion_agent',       icon: '📥', label: 'Ingestion',       desc: 'Validate & normalise' },
  { key: 'investigation_agent',   icon: '🔍', label: 'Investigation',   desc: 'Gather evidence' },
  { key: 'root_cause_agent',      icon: '🧠', label: 'Root Cause AI',   desc: 'Diagnose failure' },
  { key: 'decision_agent',        icon: '⚖️',  label: 'Decision',        desc: 'Choose resolution' },
  { key: 'auto_resolve_agent',    icon: '🤖', label: 'Auto-Resolve',    desc: 'Execute automated fix' },
  { key: 'client_outreach_agent', icon: '📧', label: 'Client Outreach', desc: 'Compose notification' },
  { key: 'compliance_agent',      icon: '🛡️', label: 'Compliance',      desc: 'Escalate to queue' },
  { key: 'manual_review_agent',   icon: '👤', label: 'Manual Review',   desc: 'Package ops dossier' },
  { key: 'egress_agent',          icon: '📤', label: 'Egress',          desc: 'Persist & seal' },
]

// Agents that are mutually exclusive execution branches
const EXECUTION_AGENTS = new Set([
  'auto_resolve_agent', 'client_outreach_agent',
  'compliance_agent', 'manual_review_agent',
])

function agentState(agentKey, events, done) {
  const hit = events.find((e) => e.agent === agentKey)
  if (hit) return 'done'
  // If any execution agent finished, other execution agents are skipped
  if (EXECUTION_AGENTS.has(agentKey)) {
    const anyExecDone = events.some((e) => EXECUTION_AGENTS.has(e.agent))
    if (anyExecDone) return 'skipped'
  }
  // Currently running = last completed agent's successor hasn't been done yet
  if (events.length > 0) {
    const lastDone = events[events.length - 1]?.agent
    const lastIdx  = ALL_AGENTS.findIndex((a) => a.key === lastDone)
    const thisIdx  = ALL_AGENTS.findIndex((a) => a.key === agentKey)
    if (thisIdx === lastIdx + 1 && !done) return 'running'
  } else if (agentKey === 'ingestion_agent' && !done) {
    return 'running'
  }
  return 'pending'
}

export default function AgentPipeline({ events, done, exceptionId }) {
  const bottomRef = useRef(null)

  // Auto-scroll log to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events])

  const latestEvent = events[events.length - 1]

  return (
    <div className={styles.root} aria-label="Agent pipeline progress">
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.headerIcon}>🔄</span>
          <div>
            <div className={styles.headerTitle}>Agent Pipeline</div>
            {exceptionId && (
              <div className={styles.headerSub}>
                <code>{exceptionId}</code>
              </div>
            )}
          </div>
        </div>
        <div className={done ? styles.doneChip : styles.runningChip}>
          {done
            ? <><span className={styles.dot} style={{ background: '#16a34a' }} />Complete</>
            : <><span className={`${styles.dot} ${styles.pulse}`} />Running</>
          }
        </div>
      </div>

      {/* Pipeline nodes */}
      <div className={styles.pipeline} role="list">
        {ALL_AGENTS.map((agent, i) => {
          const state   = agentState(agent.key, events, done)
          const ev      = events.find((e) => e.agent === agent.key)
          const isExec  = EXECUTION_AGENTS.has(agent.key)

          return (
            <div
              key={agent.key}
              className={`${styles.agentRow} ${styles[state]}`}
              role="listitem"
              aria-label={`${agent.label}: ${state}`}
            >
              {/* Connector line above (skip first) */}
              {i > 0 && (
                <div className={`${styles.connector} ${state === 'done' || state === 'running' ? styles.connectorActive : ''}`} aria-hidden="true" />
              )}

              <div className={styles.agentCard}>
                {/* Icon */}
                <div className={`${styles.agentIcon} ${styles[`icon_${state}`]}`} aria-hidden="true">
                  {state === 'running'
                    ? <span className={styles.spinIcon}>⚙️</span>
                    : state === 'done' ? <span>{agent.icon}</span>
                    : state === 'skipped' ? <span className={styles.skipIcon}>—</span>
                    : <span className={styles.pendingIcon}>{agent.icon}</span>
                  }
                </div>

                {/* Info */}
                <div className={styles.agentInfo}>
                  <div className={styles.agentName}>
                    {agent.label}
                    {isExec && state !== 'skipped' && (
                      <span className={styles.branchTag}>branch</span>
                    )}
                  </div>
                  <div className={styles.agentDesc}>
                    {state === 'running' && <span className={styles.runningLabel}>Processing...</span>}
                    {state === 'skipped' && <span className={styles.skippedLabel}>Not on this path</span>}
                    {state === 'done' && ev?.decision && (
                      <span className={styles.decisionLabel}>{ev.decision}</span>
                    )}
                    {state === 'pending' && <span className={styles.pendingLabel}>{agent.desc}</span>}
                  </div>
                </div>

                {/* Status indicator */}
                <div className={styles.stateIndicator} aria-hidden="true">
                  {state === 'done'    && <span className={styles.checkMark}>✓</span>}
                  {state === 'running' && <span className={styles.spinnerSmall} />}
                  {state === 'skipped' && <span className={styles.skipMark}>○</span>}
                  {state === 'pending' && <span className={styles.pendingMark}>·</span>}
                </div>
              </div>

              {/* Expanded detail for completed agents */}
              {state === 'done' && ev?.justification && (
                <div className={styles.agentDetail} aria-label={`${agent.label} output`}>
                  <p className={styles.justification}>{ev.justification}</p>
                  {ev.failure_type && ev.failure_type !== '' && (
                    <span className={styles.chip} style={{ background: '#fef3c7', color: '#92400e' }}>
                      {ev.failure_type.replace(/_/g, ' ')}
                    </span>
                  )}
                  {ev.resolution_action && ev.resolution_action !== '' && (
                    <span className={styles.chip} style={{ background: '#dbeafe', color: '#1d4ed8' }}>
                      → {ev.resolution_action.replace(/_/g, ' ')}
                    </span>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Live log */}
      {events.length > 0 && (
        <div className={styles.logSection} aria-label="Live agent log">
          <div className={styles.logTitle}>Live Log</div>
          <div className={styles.logBody}>
            {events.map((ev, i) => (
              <div key={i} className={styles.logLine}>
                <span className={styles.logTime}>
                  {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString('en-IN', { hour12: false }) : ''}
                </span>
                <span className={styles.logAgent}>[{ev.agent?.replace('_agent', '')}]</span>
                <span className={styles.logMsg}>{ev.label}</span>
                {ev.decision && <span className={styles.logDecision}> → {ev.decision}</span>}
              </div>
            ))}
            {!done && (
              <div className={styles.logLine}>
                <span className={styles.logTime}>{new Date().toLocaleTimeString('en-IN', { hour12: false })}</span>
                <span className={styles.logAgent}>[system]</span>
                <span className={styles.logRunning}>
                  <span className={styles.logCursor} aria-hidden="true" />
                  waiting for next agent...
                </span>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        </div>
      )}
    </div>
  )
}
