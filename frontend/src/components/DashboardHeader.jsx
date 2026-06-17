import { FiBell, FiBellOff, FiDownload, FiFileText, FiLogOut, FiMoon, FiSun, FiUser } from 'react-icons/fi'
import { useEffect, useState } from 'react'
import { getNotificationPermission, requestNotificationPermission } from '../utils/notificationHelper'

function DashboardHeader({
  analytics = {},
  darkMode,
  formatAmount,
  onDownloadReport,
  onDownloadExcel,
  onLogout,
  onProfileClick,
  onToggleDark,
  user,
}) {
  const income = Number(user?.monthly_income || 0)
  const savings = Number(user?.monthly_savings || 0)
  const budget = Number(user?.available_budget || user?.monthly_budget || 0)
  const riskScore = analytics?.risk_score || 0
  const money = formatAmount || ((amt) => `₹${Number(amt || 0).toLocaleString()}`)

  const riskLevel = riskScore >= 70 ? 'high' : riskScore >= 40 ? 'medium' : 'low'

  const [notifPermission, setNotifPermission] = useState(getNotificationPermission())
  const [notifMessage, setNotifMessage] = useState('')

  useEffect(() => {
    setNotifPermission(getNotificationPermission())
  }, [])

  useEffect(() => {
    if (!notifMessage) return
    const timer = setTimeout(() => setNotifMessage(''), 3000)
    return () => clearTimeout(timer)
  }, [notifMessage])

  async function handleNotificationClick() {
    if (notifPermission === 'denied') {
      setNotifMessage('Blocked — enable notifications in browser settings')
      return
    }
    if (notifPermission === 'granted') {
      setNotifMessage('Notifications are already enabled')
      return
    }
    const result = await requestNotificationPermission()
    setNotifPermission(result)
    setNotifMessage(
      result === 'granted'
        ? 'Notifications enabled successfully'
        : 'Notifications were not enabled'
    )
  }

  return (
    <header className="topbar">
      <div className="topbar-header">
        <div className="topbar-title">
          <p className="eyebrow">AI Budget Overspending Alert</p>
          <h1>Welcome, {user?.name}</h1>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', position: 'relative' }}>
          <button
            className="dark-toggle"
            onClick={handleNotificationClick}
            title={
              notifPermission === 'granted'
                ? 'Notifications enabled'
                : 'Click to enable budget alerts'
            }
          >
            {notifPermission === 'granted' ? <FiBell size={18} /> : <FiBellOff size={18} />}
          </button>

          {notifMessage && (
            <div
              style={{
                position: 'absolute',
                top: '110%',
                left: 0,
                background: 'var(--card)',
                color: 'var(--text-primary)',
                border: '1px solid var(--soft-border)',
                borderRadius: '8px',
                padding: '8px 12px',
                fontSize: '12px',
                boxShadow: 'var(--shadow-md)',
                whiteSpace: 'nowrap',
                zIndex: 50,
              }}
            >
              {notifMessage}
            </div>
          )}

          <button className="dark-toggle" onClick={onToggleDark} title="Toggle dark mode">
            {darkMode ? <FiSun size={18} /> : <FiMoon size={18} />}
            {darkMode ? 'Light' : 'Dark'}
          </button>

          <button className="profile-button" onClick={onProfileClick}>
            <FiUser />
            My Profile
          </button>
        </div>
      </div>

      <div className="overview-grid">
        <div className="overview-card">
          <h4>Monthly Income</h4>
          <h2>{money(income)}</h2>
        </div>

        <div className="overview-card">
          <h4>Monthly Savings</h4>
          <h2>{money(savings)}</h2>
        </div>

        <div className="overview-card">
          <h4>Total Budget</h4>
          <h2>{money(budget)}</h2>
        </div>

        <div className={`overview-card risk-card risk-${riskLevel}`}>
          <h4>Risk Score</h4>
          <h2>{riskScore}/100</h2>
          <p>
            {riskScore >= 70 ? '🔴 High Risk' : riskScore >= 40 ? '🟠 Medium Risk' : '🟢 Low Risk'}
          </p>
          {riskScore >= 70 && <p>High spending detected. Reduce non-essential expenses.</p>}
        </div>
      </div>

      <div className="topbar-actions">
        <button onClick={onDownloadReport}>
          <FiFileText /> PDF
        </button>

        <button className="secondary-button" onClick={onDownloadExcel}>
          <FiDownload /> Excel
        </button>

        <button className="icon-button" onClick={onLogout}>
          <FiLogOut />
        </button>
      </div>
    </header>
  )
}

export default DashboardHeader
