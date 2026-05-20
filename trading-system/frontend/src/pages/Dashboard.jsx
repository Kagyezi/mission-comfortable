import { useState, useEffect } from 'react'
import api from '../api/client'

/**
 * Dashboard — Phase 1
 * Shows system health check and placeholder metric cards.
 * Will be populated with live data in Phase 8 (Backend API).
 */
export default function Dashboard() {
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.get('/health')
      .then(res => setHealth(res.data))
      .catch(err => setError('Cannot reach API — is the backend running?'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="page">
      <div className="page-header">
        <h2 className="page-title">Dashboard</h2>
        <p className="page-subtitle">Portfolio overview and system status</p>
      </div>

      {/* System health banner */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-title">System Status</div>
        {loading && <p className="text-muted">Checking connection…</p>}
        {error   && (
          <div className="row">
            <span className="status-dot dot-red" />
            <span style={{ color: 'var(--color-loss)' }}>{error}</span>
          </div>
        )}
        {health && (
          <div style={{ display: 'flex', gap: 32, flexWrap: 'wrap' }}>
            <StatusItem
              label="API"
              value={health.status === 'ok' ? 'Online' : 'Error'}
              dot={health.status === 'ok' ? 'dot-green' : 'dot-red'}
            />
            <StatusItem
              label="Database"
              value={health.database === 'connected' ? 'Connected' : 'Error'}
              dot={health.database === 'connected' ? 'dot-green' : 'dot-red'}
              detail={health.database !== 'connected' ? health.database : null}
            />
            <StatusItem label="Version" value={health.version} dot="dot-gray" />
          </div>
        )}
      </div>

      {/* Portfolio metrics — placeholder until Phase 8 */}
      <div className="metrics-grid">
        <MetricCard label="Portfolio Balance"   value="—"    sub="Available in Phase 8" />
        <MetricCard label="Today's P&L"         value="—"    sub="Available in Phase 8" />
        <MetricCard label="Open Trades"         value="—"    sub="Available in Phase 8" />
        <MetricCard label="Win Rate"            value="—"    sub="Available in Phase 8" />
      </div>

      {/* Recent trades — placeholder */}
      <div className="card">
        <div className="card-title">Last 5 Closed Trades</div>
        <div className="placeholder">
          <span className="placeholder-icon">↕</span>
          <h3>No trades yet</h3>
          <p>Trades will appear here once the bot is running — Phase 5</p>
        </div>
      </div>
    </div>
  )
}

function StatusItem({ label, value, dot, detail }) {
  return (
    <div>
      <div style={{ fontSize: 11, color: 'var(--text-faint)', marginBottom: 4 }}>{label}</div>
      <div className="row" style={{ gap: 6 }}>
        <span className={`status-dot ${dot}`} />
        <span style={{ fontWeight: 600 }}>{value}</span>
      </div>
      {detail && <div style={{ fontSize: 11, color: 'var(--color-loss)', marginTop: 2 }}>{detail}</div>}
    </div>
  )
}

function MetricCard({ label, value, sub }) {
  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      {sub && <div className="metric-sub">{sub}</div>}
    </div>
  )
}
