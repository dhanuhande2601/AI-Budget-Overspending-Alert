import { FiDownload, FiFileText, FiLogOut, FiMoon, FiSun, FiUser } from 'react-icons/fi'

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
  const money = formatAmount || ((amt) => `Rs. ${Number(amt || 0).toLocaleString()}`)

  const riskLevel = riskScore >= 70 ? 'high' : riskScore >= 40 ? 'medium' : 'low'

  return (
    <header className="topbar">
      <div className="topbar-header">
        <div className="topbar-title">
          <p className="eyebrow">AI Budget Overspending Alert</p>
          <h1>Welcome, {user?.name}</h1>
        </div>

        <div className="topbar-controls">
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
            {riskScore >= 70 ? 'High Risk' : riskScore >= 40 ? 'Medium Risk' : 'Low Risk'}
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
