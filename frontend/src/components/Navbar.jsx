import React from 'react'
import { LayoutDashboard, List, BarChart3, Plus, Building2, Bot } from 'lucide-react'
import styles from './Navbar.module.css'

const NAV_ITEMS = [
  { key: 'dashboard', label: 'Dashboard',    icon: LayoutDashboard },
  { key: 'submit',    label: 'New Exception', icon: Plus           },
  { key: 'list',      label: 'Exceptions',    icon: List           },
  { key: 'agents',    label: 'Agents',        icon: Bot            },
  { key: 'metrics',   label: 'Analytics',     icon: BarChart3      },
]

export default function Navbar({ currentView, navigate }) {
  return (
    <nav className={styles.nav} role="navigation" aria-label="Main navigation">
      {/* Bank brand */}
      <div className={styles.brand} onClick={() => navigate('dashboard')} role="button" tabIndex={0}
           onKeyDown={(e) => e.key === 'Enter' && navigate('dashboard')}
           aria-label="Go to dashboard">
        <div className={styles.logoMark}>
          <Building2 size={22} color="var(--gold-400)" />
        </div>
        <div className={styles.brandText}>
          <span className={styles.bankName}>First National Bank</span>
          <span className={styles.systemName}>Payment Exception Resolution</span>
        </div>
      </div>

      {/* Nav links */}
      <ul className={styles.navList} role="list">
        {NAV_ITEMS.map(({ key, label, icon: Icon }) => (
          <li key={key}>
            <button
              className={`${styles.navBtn} ${currentView === key ? styles.active : ''}`}
              onClick={() => navigate(key)}
              aria-current={currentView === key ? 'page' : undefined}
            >
              <Icon size={16} aria-hidden="true" />
              <span>{label}</span>
            </button>
          </li>
        ))}
      </ul>

      {/* User info stub */}
      <div className={styles.userArea}>
        <div className={styles.avatar} aria-label="Logged in as Operations Analyst">OA</div>
        <div className={styles.userInfo}>
          <span className={styles.userName}>Ops Analyst</span>
          <span className={styles.userRole}>Payment Operations</span>
        </div>
      </div>
    </nav>
  )
}
