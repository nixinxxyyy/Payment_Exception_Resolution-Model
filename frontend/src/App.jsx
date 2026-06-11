import React, { useState } from 'react'
import Navbar from './components/Navbar.jsx'
import Dashboard from './components/Dashboard.jsx'
import SubmitException from './components/SubmitException.jsx'
import ExceptionList from './components/ExceptionList.jsx'
import ExceptionDetail from './components/ExceptionDetail.jsx'
import MetricsPanel from './components/MetricsPanel.jsx'
import AgentsWorkflow from './components/AgentsWorkflow.jsx'
import styles from './App.module.css'

const VIEWS = {
  DASHBOARD:  'dashboard',
  SUBMIT:     'submit',
  LIST:       'list',
  DETAIL:     'detail',
  METRICS:    'metrics',
  AGENTS:     'agents',
}

export default function App() {
  const [view, setView]                 = useState(VIEWS.DASHBOARD)
  const [selectedExceptionId, setSelectedId] = useState(null)

  const navigate = (v, id = null) => {
    setView(v)
    if (id) setSelectedId(id)
  }

  return (
    <div className={styles.appRoot}>
      <Navbar currentView={view} navigate={navigate} />
      <main className={styles.main}>
        {view === VIEWS.DASHBOARD && (
          <Dashboard navigate={navigate} VIEWS={VIEWS} />
        )}
        {view === VIEWS.SUBMIT && (
          <SubmitException navigate={navigate} VIEWS={VIEWS} />
        )}
        {view === VIEWS.LIST && (
          <ExceptionList
            navigate={navigate}
            VIEWS={VIEWS}
            onSelect={(id) => navigate(VIEWS.DETAIL, id)}
          />
        )}
        {view === VIEWS.DETAIL && selectedExceptionId && (
          <ExceptionDetail
            exceptionId={selectedExceptionId}
            navigate={navigate}
            VIEWS={VIEWS}
          />
        )}
        {view === VIEWS.METRICS && (
          <MetricsPanel />
        )}
        {view === VIEWS.AGENTS && (
          <AgentsWorkflow />
        )}
      </main>
      <footer className={styles.footer}>
        <span>© 2024 First National Bank · Payment Exception Resolution Model</span>
        <span>Powered by AI Multi-Agent System v2.0</span>
      </footer>
    </div>
  )
}
