import { NavLink } from 'react-router-dom'

const navItems = [
  { to: '/',        icon: '▦',  label: 'Dashboard'      },
  { to: '/bots',    icon: '⬡',  label: 'Bots'           },
  { to: '/trades',  icon: '↕',  label: 'Trade Log'      },
  { to: '/charts',  icon: '◈',  label: 'Charts'         },
  { to: '/risk',    icon: '⊛',  label: 'Risk Settings'  },
  { to: '/system',  icon: '◉',  label: 'System Monitor' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>⟠ TradingOS</h1>
        <p>Algorithmic Trading System</p>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-label">Navigation</div>
        {navItems.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>

      <div style={{ padding: '14px 18px', borderTop: '1px solid var(--border)' }}>
        <div style={{ fontSize: 11, color: 'var(--text-faint)' }}>
          v0.1.0 · Phase 1
        </div>
      </div>
    </aside>
  )
}
