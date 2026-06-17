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

  const riskStyle = {
    background: riskScore >= 70 ? '#fef2f2' : riskScore >= 40 ? '#fffbeb' : '#f0fdf4',
    color:      riskScore >= 70 ? '#dc2626' : riskScore >= 40 ? '#d97706' : '#16a34a',
    border: `1px solid ${riskScore >= 70 ? '#fecaca' : riskScore >= 40 ? '#fde68a' : '#bbf7d0'}`,
  }

  const [notifPermission, setNotifPermission] = useState(getNotificationPermission())

  useEffect(() => {
    setNotifPermission(getNotificationPermission())
  }, [])

  async function handleNotificationClick() {
    if (notifPermission === 'denied') {
      alert('Notifications are blocked. Please enable them in your browser settings.')
      return
    }
    const result = await requestNotificationPermission()
    setNotifPermission(result)
  }

  return (
    <header className="topbar">
      <div className="topbar-header">
        <div className="topbar-title">
          <p className="eyebrow">AI Budget Overspending Alert</p>
          <h1>Welcome, {user?.name}</h1>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
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

        <div className="overview-card risk-card" style={riskStyle}>
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
