import {
  FiDownload,
  FiFileText,
  FiLogOut,
} from 'react-icons/fi'

function DashboardHeader({
  analytics = {},
  onDownloadReport,
  onDownloadExcel,
  onLogout,
  onProfileClick,
  user,
}) {

  const income = Number(user?.monthly_income || 0)
  const savings = Number(user?.monthly_savings || 0)
  const budget = Number(
    user?.available_budget || user?.monthly_budget || 0
  )

  return (
    <header className="topbar">

      <div className="topbar-title" onClick={onProfileClick} style={{ cursor: 'pointer' }}>
        <p className="eyebrow">
          AI Budget Overspending Alert
        </p>

        <h1>
          Welcome, {user?.name}
        </h1>
      </div>

      <div className="overview-grid">

        <div className="overview-card">
          <h4>Monthly Income</h4>
          <h2>₹{income}</h2>
        </div>

        <div className="overview-card">
          <h4>Monthly Savings</h4>
          <h2>₹{savings}</h2>
        </div>

        <div className="overview-card">
          <h4>Total Budget</h4>
          <h2>₹{budget}</h2>
        </div>

        <div className="overview-card risk-card">
          <h4>Risk Score</h4>
          <h2>
            {analytics?.risk_score || 0}/100
          </h2>
          <p>
            {analytics?.risk_level || 'SAFE'}
          </p>
        </div>

      </div>

      <div className="topbar-actions">

        <button onClick={onDownloadReport}>
          <FiFileText />
          PDF
        </button>

        <button
          className="secondary-button"
          onClick={onDownloadExcel}
        >
          <FiDownload />
          Excel
        </button>

        <button
          className="icon-button"
          onClick={onLogout}
        >
          <FiLogOut />
        </button>

      </div>

    </header>
  )
}

export default DashboardHeader