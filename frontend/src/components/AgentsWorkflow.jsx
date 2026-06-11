import React, { useState } from 'react'
import styles from './AgentsWorkflow.module.css'

// ── Agent catalogue data ───────────────────────────────────────────────────
const AGENTS = [
  {
    id: 'ingestion_agent',
    number: '01',
    icon: '📥',
    name: 'Ingestion Agent',
    role: 'Gateway & Deduplication',
    color: '#163468',
    tagColor: { bg: '#dbeafe', text: '#1d4ed8' },
    purpose:
      'First agent in the workflow. Receives every incoming payment exception event, validates and normalises all fields, detects duplicate exception triggers (idempotency), and prepares the state for downstream agents.',
    contract: {
      inputs:  ['payment_id', 'client_id', 'account_id', 'payment_rail', 'amount', 'currency', 'beneficiary_details', 'failure_code', 'failure_message'],
      outputs: ['Normalised state fields', 'is_duplicate_event flag', 'Enriched metadata', 'First audit entry'],
    },
    authority: 'Accept or suppress duplicate events. Normalise fields. Cannot modify business logic.',
    dependencies: ['None — entry point'],
    triggers: ['investigation_agent (normal path)', 'egress_agent (duplicate short-circuit)'],
  },
  {
    id: 'investigation_agent',
    number: '02',
    icon: '🔍',
    name: 'Investigation Agent',
    role: 'Evidence Gathering',
    color: '#0891b2',
    tagColor: { bg: '#cffafe', text: '#0e7490' },
    purpose:
      'Gathers all evidence needed to diagnose the root cause. Runs 7 parallel checks: account balance, beneficiary detail validation, duplicate payment detection, network/rail status, AML/compliance flags, rail cut-off time, and prior retry history.',
    contract: {
      inputs:  ['Normalised state from Ingestion Agent'],
      outputs: ['balance_check', 'beneficiary_valid', 'duplicate_of', 'network_status', 'compliance_flags', 'is_within_cutoff', 'prior_retry_records', 'evidence_gathered[]'],
    },
    authority: 'Read-only data access to ledger, beneficiary directory, network status, and compliance APIs. Cannot modify payment records.',
    dependencies: ['Ingestion Agent'],
    triggers: ['Root Cause Agent'],
  },
  {
    id: 'root_cause_agent',
    number: '03',
    icon: '🧠',
    name: 'Root Cause Agent',
    role: 'AI Diagnosis (GPT-4o)',
    color: '#7c3aed',
    tagColor: { bg: '#ede9fe', text: '#5b21b6' },
    purpose:
      'Uses GPT-4o with structured evidence to diagnose the exact failure type. Determines whether automated correction is safe (idempotency check). Falls back to fast-path code mapping for clear-cut failure codes before calling the LLM.',
    contract: {
      inputs:  ['All evidence from Investigation Agent', 'failure_code', 'failure_message'],
      outputs: ['failure_type (enum)', 'root_cause_summary', 'is_safe_to_automate (bool)', 'decision_confidence (0–1)'],
    },
    authority: 'Diagnose and classify only. Cannot trigger any downstream actions. Hard-overrides automation safety for COMPLIANCE_HOLD, UNCERTAIN_RETRY_STATUS, INSUFFICIENT_FUNDS.',
    dependencies: ['Investigation Agent', 'OpenAI GPT-4o API'],
    triggers: ['Decision Agent'],
  },
  {
    id: 'decision_agent',
    number: '04',
    icon: '⚖️',
    name: 'Decision Agent',
    role: 'Resolution Orchestrator',
    color: '#d97706',
    tagColor: { bg: '#fef3c7', text: '#92400e' },
    purpose:
      'Applies a deterministic rule-based decision tree first (covering 7 hard-coded rules for each failure type). Falls through to GPT-4o only for ambiguous cases. Applies a safety override: if the chosen action is AUTO_RETRY or AUTO_CORRECT but is_safe_to_automate is false, it downgrades to MANUAL_REVIEW.',
    contract: {
      inputs:  ['failure_type', 'is_safe_to_automate', 'compliance_flags', 'network_status', 'retry_count', 'balance_check'],
      outputs: ['resolution_action (enum)', 'decision_rationale', 'status → DECIDED'],
    },
    authority: 'Choose resolution action. Apply safety overrides. Cannot execute any actions — delegates to execution agents.',
    dependencies: ['Root Cause Agent'],
    triggers: ['Auto-Resolve Agent', 'Client Outreach Agent', 'Compliance Agent', 'Manual Review Agent'],
  },
  {
    id: 'auto_resolve_agent',
    number: '05',
    icon: '🤖',
    name: 'Auto-Resolve Agent',
    role: 'Automated Execution',
    color: '#16a34a',
    tagColor: { bg: '#dcfce7', text: '#15803d' },
    purpose:
      'Executes automated resolution actions without human involvement. Handles four action types: AUTO_RETRY (resubmit with idempotency key), AUTO_CORRECT (fix minor beneficiary details and retry), DUPLICATE_SUPPRESS (safely cancel the duplicate), HOLD_FOR_WINDOW (schedule for next rail processing cycle).',
    contract: {
      inputs:  ['resolution_action ∈ {AUTO_RETRY, AUTO_CORRECT, DUPLICATE_SUPPRESS, HOLD_FOR_WINDOW}', 'beneficiary_details', 'retry_count'],
      outputs: ['execution_result', 'status → EXECUTING | CANCELLED | HELD', 'scheduled_retry_at (if HOLD)'],
    },
    authority: 'Call payment gateway API for retry/cancel. Increment retry_count. Schedule deferred retries. Cannot handle compliance cases.',
    dependencies: ['Decision Agent'],
    triggers: ['Egress Agent'],
  },
  {
    id: 'client_outreach_agent',
    number: '06',
    icon: '📧',
    name: 'Client Outreach Agent',
    role: 'Customer Communication',
    color: '#0891b2',
    tagColor: { bg: '#cffafe', text: '#0e7490' },
    purpose:
      'Generates a professional, empathetic banking communication for cases that require client input (INSUFFICIENT_FUNDS, INCORRECT_BENEFICIARY major mismatch, unknown failures). Uses GPT-4o to compose context-aware messages in formal banking language, then queues them to the notification service.',
    contract: {
      inputs:  ['resolution_action = CLIENT_OUTREACH', 'failure_type', 'amount', 'currency', 'root_cause_summary'],
      outputs: ['client_message (full email text)', 'execution_result (delivery status)', 'status → AWAITING_INPUT'],
    },
    authority: 'Compose and queue client notifications via email/SMS/push. Cannot make payment decisions or access account funds.',
    dependencies: ['Decision Agent', 'OpenAI GPT-4o API'],
    triggers: ['Egress Agent'],
  },
  {
    id: 'compliance_agent',
    number: '07',
    icon: '🛡️',
    name: 'Compliance Agent',
    role: 'Regulatory Escalation',
    color: '#9f1239',
    tagColor: { bg: '#ffe4e6', text: '#9f1239' },
    purpose:
      'Handles all compliance-related escalations (AML, sanctions, high-value regulatory holds). Routes to the correct compliance sub-queue (AML_REVIEW, SANCTIONS_REVIEW, HIGH_VALUE_REVIEW). Uses GPT-4o to generate a structured compliance case dossier. Locks the payment from any automated retry.',
    contract: {
      inputs:  ['resolution_action = COMPLIANCE_REVIEW', 'compliance_flags[]', 'amount', 'beneficiary_details', 'failure_type'],
      outputs: ['escalation_queue (target queue)', 'execution_result (dossier + lock)', 'client_message (generic hold notice)', 'status → ESCALATED'],
    },
    authority: 'Lock payment from automated retry. Assign to compliance queue. Generate compliance dossier. Cannot release holds.',
    dependencies: ['Decision Agent', 'OpenAI GPT-4o API'],
    triggers: ['Egress Agent'],
  },
  {
    id: 'manual_review_agent',
    number: '08',
    icon: '👤',
    name: 'Manual Review Agent',
    role: 'Operations Escalation',
    color: '#64748b',
    tagColor: { bg: '#f1f5f9', text: '#475569' },
    purpose:
      'Packages uncertain or unresolvable cases for the operations team. Determines priority tier (P1/P2/P3), assigns to the correct ops queue (HIGH_VALUE, RETRY_INVESTIGATION, EXHAUSTED_RETRY, GENERAL_OPS), sets SLA deadline, and builds a complete case dossier for the analyst.',
    contract: {
      inputs:  ['resolution_action ∈ {MANUAL_REVIEW, CANCEL}', 'failure_type', 'amount', 'retry_count', 'compliance_flags'],
      outputs: ['escalation_queue (ops queue)', 'execution_result (dossier + priority + SLA)', 'client_message', 'status → ESCALATED'],
    },
    authority: 'Assign priority, queue, and SLA. Build ops dossier. Lock payment. Cannot resolve payments.',
    dependencies: ['Decision Agent'],
    triggers: ['Egress Agent'],
  },
  {
    id: 'egress_agent',
    number: '09',
    icon: '📤',
    name: 'Egress Agent',
    role: 'Persistence & Seal',
    color: '#334155',
    tagColor: { bg: '#f1f5f9', text: '#334155' },
    purpose:
      'Final agent in all paths. Persists the complete resolved state to MySQL (upsert pattern for idempotency), delivers outputs to downstream systems, emits structured observability metrics, and seals the audit trail with an immutable final entry.',
    contract: {
      inputs:  ['Complete resolved PaymentExceptionState from any execution agent'],
      outputs: ['MySQL persistence (payment_exceptions + audit_logs + retry_attempts + client_notifications)', 'Sealed audit trail', 'Observability metrics'],
    },
    authority: 'Write to MySQL. Deliver to notification service and case queues. Cannot modify decisions or re-route.',
    dependencies: ['Any of: Auto-Resolve, Client Outreach, Compliance, Manual Review Agents', 'MySQL database'],
    triggers: ['END'],
  },
]

// ── Workflow diagram data ──────────────────────────────────────────────────
const FLOW_NODES = [
  { id: 'input',       label: 'Payment\nException Input',  type: 'io',        x: 340, y: 20  },
  { id: 'ingestion',   label: '01 Ingestion',               type: 'agent',     x: 340, y: 100 },
  { id: 'dedup',       label: 'Duplicate\nEvent?',          type: 'decision',  x: 340, y: 200 },
  { id: 'investigation',label: '02 Investigation',          type: 'agent',     x: 340, y: 300 },
  { id: 'rootcause',   label: '03 Root Cause\nAnalysis',    type: 'agent',     x: 340, y: 400 },
  { id: 'decision',    label: '04 Decision',                type: 'agent',     x: 340, y: 500 },
  { id: 'fan',         label: 'Route by\nResolution Action',type: 'decision',  x: 340, y: 600 },
  // execution branches
  { id: 'auto',        label: '05 Auto-Resolve',            type: 'exec',      x: 60,  y: 720 },
  { id: 'outreach',    label: '06 Client\nOutreach',        type: 'exec',      x: 220, y: 720 },
  { id: 'compliance',  label: '07 Compliance\nEscalation',  type: 'exec',      x: 400, y: 720 },
  { id: 'manual',      label: '08 Manual\nReview',          type: 'exec',      x: 580, y: 720 },
  // converge
  { id: 'egress',      label: '09 Egress',                  type: 'agent',     x: 340, y: 840 },
  { id: 'mysql',       label: 'MySQL\nDatabase',            type: 'store',     x: 560, y: 920 },
  { id: 'end',         label: 'END',                        type: 'io',        x: 340, y: 940 },
]

export default function AgentsWorkflow() {
  const [activeAgent, setActiveAgent] = useState(null)
  const [activeTab, setActiveTab]     = useState('catalogue') // 'catalogue' | 'workflow'

  const selected = AGENTS.find((a) => a.id === activeAgent)

  return (
    <div className={styles.root}>
      {/* Page header */}
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.title}>Agent Catalogue & Workflow</h1>
          <p className={styles.subtitle}>
            9 specialised AI agents working in sequence to diagnose and resolve failed payment transactions
          </p>
        </div>
        <div className={styles.countBadge}>9 Agents · 4 Execution Branches</div>
      </div>

      {/* Tabs */}
      <div className={styles.tabBar} role="tablist">
        <button
          role="tab" aria-selected={activeTab === 'catalogue'}
          className={`${styles.tab} ${activeTab === 'catalogue' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('catalogue')}
        >
          🗂️ Agent Catalogue
        </button>
        <button
          role="tab" aria-selected={activeTab === 'workflow'}
          className={`${styles.tab} ${activeTab === 'workflow' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('workflow')}
        >
          🔀 Workflow Diagram
        </button>
      </div>

      {/* ── CATALOGUE TAB ── */}
      {activeTab === 'catalogue' && (
        <div className={styles.catalogueLayout}>
          {/* Agent grid */}
          <div className={styles.agentGrid}>
            {AGENTS.map((agent) => (
              <button
                key={agent.id}
                className={`${styles.agentCard} ${activeAgent === agent.id ? styles.agentCardActive : ''}`}
                onClick={() => setActiveAgent(activeAgent === agent.id ? null : agent.id)}
                style={{ '--agent-color': agent.color }}
                aria-expanded={activeAgent === agent.id}
                aria-controls={`agent-detail-${agent.id}`}
              >
                <div className={styles.cardTop}>
                  <span className={styles.agentNumber}>{agent.number}</span>
                  <span className={styles.agentIconLg}>{agent.icon}</span>
                </div>
                <div className={styles.cardBody}>
                  <div className={styles.agentName}>{agent.name}</div>
                  <span
                    className={styles.roleTag}
                    style={{ background: agent.tagColor.bg, color: agent.tagColor.text }}
                  >
                    {agent.role}
                  </span>
                </div>
                <div className={styles.cardArrow}>{activeAgent === agent.id ? '▲' : '▼'}</div>
              </button>
            ))}
          </div>

          {/* Detail panel */}
          {selected && (
            <div
              className={styles.detailPanel}
              id={`agent-detail-${selected.id}`}
              style={{ '--agent-color': selected.color }}
              aria-label={`${selected.name} details`}
            >
              <div className={styles.detailHeader}>
                <div className={styles.detailIconWrap}>
                  <span className={styles.detailIcon}>{selected.icon}</span>
                </div>
                <div>
                  <div className={styles.detailNumber}>Agent {selected.number}</div>
                  <h2 className={styles.detailName}>{selected.name}</h2>
                  <span
                    className={styles.detailRole}
                    style={{ background: selected.tagColor.bg, color: selected.tagColor.text }}
                  >
                    {selected.role}
                  </span>
                </div>
              </div>

              <Section title="Purpose">
                <p className={styles.purposeText}>{selected.purpose}</p>
              </Section>

              <Section title="Contract">
                <div className={styles.contractGrid}>
                  <div>
                    <div className={styles.contractLabel}>📨 Inputs</div>
                    <ul className={styles.contractList}>
                      {selected.contract.inputs.map((i, idx) => (
                        <li key={idx}><code className={styles.codeChip}>{i}</code></li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <div className={styles.contractLabel}>📤 Outputs</div>
                    <ul className={styles.contractList}>
                      {selected.contract.outputs.map((o, idx) => (
                        <li key={idx}><code className={styles.codeChip}>{o}</code></li>
                      ))}
                    </ul>
                  </div>
                </div>
              </Section>

              <Section title="Authority & Constraints">
                <p className={styles.authorityText}>{selected.authority}</p>
              </Section>

              <div className={styles.depsRow}>
                <div className={styles.depsBlock}>
                  <div className={styles.depsLabel}>⬅ Depends On</div>
                  <div className={styles.depsList}>
                    {selected.dependencies.map((d, i) => (
                      <span key={i} className={styles.depChip}>{d}</span>
                    ))}
                  </div>
                </div>
                <div className={styles.depsBlock}>
                  <div className={styles.depsLabel}>➡ Triggers</div>
                  <div className={styles.depsList}>
                    {selected.triggers.map((t, i) => (
                      <span key={i} className={`${styles.depChip} ${styles.triggerChip}`}>{t}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {!selected && (
            <div className={styles.detailEmpty}>
              <span className={styles.detailEmptyIcon}>👆</span>
              <p>Click any agent card to view its full specification</p>
            </div>
          )}
        </div>
      )}

      {/* ── WORKFLOW TAB ── */}
      {activeTab === 'workflow' && (
        <div className={styles.workflowTab}>
          <WorkflowDiagram />
        </div>
      )}
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div className={styles.section}>
      <div className={styles.sectionTitle}>{title}</div>
      {children}
    </div>
  )
}

// ── SVG Workflow Diagram ───────────────────────────────────────────────────
function WorkflowDiagram() {
  const [hovered, setHovered] = useState(null)

  // Node definitions: [id, x, y, w, h, label, type, color]
  const nodes = [
    // type: io | agent | decision | exec | store
    { id: 'input',        x: 275, y: 10,  w: 190, h: 40,  label: 'Payment Exception Input',    type: 'io'       },
    { id: 'ingestion',    x: 225, y: 80,  w: 290, h: 50,  label: '01  Ingestion Agent',         type: 'agent',  color: '#163468' },
    { id: 'dedup',        x: 275, y: 160, w: 190, h: 44,  label: 'Duplicate Event?',            type: 'decision' },
    { id: 'investigation',x: 215, y: 234, w: 310, h: 50,  label: '02  Investigation Agent',     type: 'agent',  color: '#0e7490' },
    { id: 'rootcause',    x: 215, y: 314, w: 310, h: 50,  label: '03  Root Cause Agent  🧠 AI', type: 'agent',  color: '#5b21b6' },
    { id: 'decision',     x: 215, y: 394, w: 310, h: 50,  label: '04  Decision Agent',          type: 'agent',  color: '#b45309' },
    { id: 'fan',          x: 255, y: 474, w: 230, h: 44,  label: 'Route by Resolution Action',  type: 'decision' },
    // exec branches
    { id: 'auto',         x: 10,  y: 558, w: 155, h: 56,  label: '05  Auto-Resolve\nAgent',     type: 'exec',   color: '#15803d' },
    { id: 'outreach',     x: 185, y: 558, w: 155, h: 56,  label: '06  Client\nOutreach Agent',  type: 'exec',   color: '#0e7490' },
    { id: 'compliance',   x: 360, y: 558, w: 155, h: 56,  label: '07  Compliance\nAgent',       type: 'exec',   color: '#9f1239' },
    { id: 'manual',       x: 535, y: 558, w: 155, h: 56,  label: '08  Manual\nReview Agent',    type: 'exec',   color: '#475569' },
    // egress
    { id: 'egress',       x: 215, y: 654, w: 310, h: 50,  label: '09  Egress Agent',            type: 'agent',  color: '#1e293b' },
    // outputs
    { id: 'mysql',        x: 520, y: 734, w: 160, h: 40,  label: '🗄  MySQL Database',           type: 'store'  },
    { id: 'audit',        x: 60,  y: 734, w: 160, h: 40,  label: '📋  Audit Trail Sealed',       type: 'store'  },
    { id: 'end',          x: 270, y: 734, w: 200, h: 40,  label: 'END',                          type: 'io'     },
  ]

  // Edges: [fromId, toId, label?, style?]
  const edges = [
    { from: 'input',        to: 'ingestion'                          },
    { from: 'ingestion',    to: 'dedup'                              },
    { from: 'dedup',        to: 'investigation', label: 'new event'  },
    { from: 'dedup',        to: 'egress',        label: 'duplicate → skip', dashed: true, offsetX: 130 },
    { from: 'investigation',to: 'rootcause'                          },
    { from: 'rootcause',    to: 'decision'                           },
    { from: 'decision',     to: 'fan'                                },
    { from: 'fan',          to: 'auto',          label: 'AUTO_RETRY\nAUTO_CORRECT\nHOLD\nSUPPRESS' },
    { from: 'fan',          to: 'outreach',      label: 'CLIENT\nOUTREACH'  },
    { from: 'fan',          to: 'compliance',    label: 'COMPLIANCE\nREVIEW' },
    { from: 'fan',          to: 'manual',        label: 'MANUAL\nREVIEW'    },
    { from: 'auto',         to: 'egress'                             },
    { from: 'outreach',     to: 'egress'                             },
    { from: 'compliance',   to: 'egress'                             },
    { from: 'manual',       to: 'egress'                             },
    { from: 'egress',       to: 'mysql'                              },
    { from: 'egress',       to: 'audit'                              },
    { from: 'egress',       to: 'end'                                },
  ]

  const nodeMap = Object.fromEntries(nodes.map((n) => [n.id, n]))

  // Compute edge path from node centre-bottom to node centre-top
  function edgePath(e) {
    const from = nodeMap[e.from]
    const to   = nodeMap[e.to]
    if (!from || !to) return ''

    const fx = from.x + from.w / 2 + (e.offsetX || 0)
    const fy = from.y + from.h
    const tx = to.x   + to.w   / 2
    const ty = to.y

    // Straight vertical
    if (Math.abs(fx - tx) < 8) {
      return `M ${fx} ${fy} L ${tx} ${ty}`
    }
    // Curved path
    const my = (fy + ty) / 2
    return `M ${fx} ${fy} C ${fx} ${my}, ${tx} ${my}, ${tx} ${ty}`
  }

  const NODE_COLORS = {
    io:       { fill: '#f8fafc', stroke: '#94a3b8', text: '#334155' },
    decision: { fill: '#fef3c7', stroke: '#d97706', text: '#92400e' },
    store:    { fill: '#f0fdf4', stroke: '#16a34a', text: '#15803d' },
  }

  return (
    <div className={styles.svgWrap}>
      <div className={styles.svgLegend}>
        <LegendItem color="#163468" label="Core Agent" />
        <LegendItem color="#15803d" label="Execution Agent (branch)" />
        <LegendItem color="#fef3c7" stroke="#d97706" label="Decision / Router" />
        <LegendItem color="#f0fdf4" stroke="#16a34a" label="Data Store / Output" />
        <LegendItem dashed label="Short-circuit (duplicate)" />
      </div>

      <svg
        viewBox="0 0 740 790"
        className={styles.svg}
        aria-label="Agent workflow diagram"
        role="img"
      >
        <defs>
          <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#94a3b8" />
          </marker>
          <marker id="arrowGold" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#c9a227" />
          </marker>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* Edges */}
        {edges.map((e, i) => {
          const d = edgePath(e)
          const isHov = hovered === e.from || hovered === e.to
          return (
            <g key={i}>
              <path
                d={d}
                fill="none"
                stroke={isHov ? '#c9a227' : '#cbd5e1'}
                strokeWidth={isHov ? 2.5 : 1.5}
                strokeDasharray={e.dashed ? '6 3' : undefined}
                markerEnd={isHov ? 'url(#arrowGold)' : 'url(#arrow)'}
                style={{ transition: 'stroke 0.2s, stroke-width 0.2s' }}
              />
              {e.label && (() => {
                const from = nodeMap[e.from]
                const to   = nodeMap[e.to]
                if (!from || !to) return null
                const lx = (from.x + from.w / 2 + to.x + to.w / 2) / 2 + (e.offsetX || 0) / 2
                const ly = (from.y + from.h + to.y) / 2
                return (
                  <text x={lx} y={ly} className={styles.edgeLabel} textAnchor="middle">
                    {e.label.split('\n').map((line, li) => (
                      <tspan key={li} x={lx} dy={li === 0 ? 0 : 12}>{line}</tspan>
                    ))}
                  </text>
                )
              })()}
            </g>
          )
        })}

        {/* Nodes */}
        {nodes.map((n) => {
          const isHov  = hovered === n.id
          const cfg    = NODE_COLORS[n.type] || {}
          const fill   = n.color || cfg.fill || '#f8fafc'
          const stroke = isHov ? '#c9a227' : (n.type === 'agent' || n.type === 'exec' ? 'transparent' : cfg.stroke || '#94a3b8')
          const textCol= n.type === 'agent' || n.type === 'exec' ? '#ffffff' : cfg.text || '#334155'
          const r      = n.type === 'decision' ? 8 : 6

          return (
            <g
              key={n.id}
              onMouseEnter={() => setHovered(n.id)}
              onMouseLeave={() => setHovered(null)}
              style={{ cursor: 'default' }}
              role="listitem"
              aria-label={n.label.replace('\n', ' ')}
            >
              <rect
                x={n.x} y={n.y} width={n.w} height={n.h}
                rx={r} ry={r}
                fill={fill}
                stroke={stroke}
                strokeWidth={isHov ? 2 : n.type === 'decision' ? 1.5 : 0}
                filter={isHov ? 'url(#glow)' : undefined}
                style={{ transition: 'filter 0.2s' }}
              />
              {/* Node text */}
              {n.label.split('\n').map((line, li, arr) => {
                const totalLines = arr.length
                const lineH      = 14
                const startY     = n.y + n.h / 2 - ((totalLines - 1) * lineH) / 2
                return (
                  <text
                    key={li}
                    x={n.x + n.w / 2}
                    y={startY + li * lineH}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fill={textCol}
                    fontSize={n.type === 'io' ? 11 : n.type === 'decision' ? 10 : 12}
                    fontWeight={n.type === 'agent' || n.type === 'exec' ? 600 : 400}
                    fontFamily="Inter, sans-serif"
                  >
                    {line}
                  </text>
                )
              })}
            </g>
          )
        })}

        {/* Hover tooltip */}
        {hovered && (() => {
          const n = nodeMap[hovered]
          if (!n || n.type === 'io' || n.type === 'decision') return null
          const agent = AGENTS.find((a) => n.id.startsWith(a.id.split('_')[0]))
          if (!agent) return null
          return (
            <g>
              <rect x={n.x + n.w + 8} y={n.y} width={180} height={54} rx={6}
                fill="#0d1f3c" stroke="#c9a227" strokeWidth={1} />
              <text x={n.x + n.w + 18} y={n.y + 18} fill="#c9a227"
                fontSize={11} fontWeight={700} fontFamily="Inter, sans-serif">
                {agent.name}
              </text>
              <text x={n.x + n.w + 18} y={n.y + 32} fill="#94a3b8"
                fontSize={9} fontFamily="Inter, sans-serif">
                {agent.role}
              </text>
              <text x={n.x + n.w + 18} y={n.y + 46} fill="#64748b"
                fontSize={9} fontFamily="Inter, sans-serif">
                Click catalogue for details
              </text>
            </g>
          )
        })()}
      </svg>
    </div>
  )
}

function LegendItem({ color, stroke, label, dashed }) {
  return (
    <div className={styles.legendItem}>
      {dashed
        ? <svg width={28} height={12}><line x1={0} y1={6} x2={28} y2={6} stroke="#94a3b8" strokeWidth={1.5} strokeDasharray="4 2" /></svg>
        : <div className={styles.legendBox} style={{ background: color, border: `1.5px solid ${stroke || color}` }} />
      }
      <span>{label}</span>
    </div>
  )
}
