import {
  FiDownload,
  FiFileText,
  FiLogOut,
  FiUser,
} from 'react-icons/fi'

function DashboardHeader({
  analytics = {},
  onDownloadReport,
  onDownloadExcel,
  onLogout,
  onProfileClick,
  user,
}) {

  const income = Number(
    user?.monthly_income || 0
  )

  const savings = Number(
    user?.monthly_savings || 0
  )

  const budget = Number(
    user?.available_budget ||
    user?.monthly_budget ||
    0
  )

  return (
    <header className="topbar">

      <div className="topbar-header">

        <div className="topbar-title">

          <p className="eyebrow">
            AI Budget Overspending Alert
          </p>

          <h1>
            Welcome, {user?.name}
          </h1>

        </div>

        <button
          className="profile-button"
          onClick={onProfileClick}
        >
          <FiUser />
          My Profile
        </button>

      </div>

      <div className="overview-grid">

        <div className="overview-card">
          <h4>Monthly Income</h4>
          <h2>
            ₹{income.toLocaleString()}
          </h2>
        </div>

        <div className="overview-card">
          <h4>Monthly Savings</h4>
          <h2>
            ₹{savings.toLocaleString()}
          </h2>
        </div>

        <div className="overview-card">
          <h4>Total Budget</h4>
          <h2>
            ₹{budget.toLocaleString()}
          </h2>
        </div>

        <div
          className="overview-card risk-card"
          style={{
            background:
              (analytics?.risk_score || 0) >= 70
                ? "#fef2f2"   // very light red
                : (analytics?.risk_score || 0) >= 40
                ? "#fffbeb"   // very light yellow
                : "#f0fdf4",  // very light green

            color:
              (analytics?.risk_score || 0) >= 70
                ? "#dc2626"
                : (analytics?.risk_score || 0) >= 40
                ? "#d97706"
                : "#16a34a",

            border: `1px solid ${
              (analytics?.risk_score || 0) >= 70
                ? "#fecaca"
                : (analytics?.risk_score || 0) >= 40
                ? "#fde68a"
                : "#bbf7d0"
            }`
          }}
        >
          <h4>Risk Score</h4>

          <h2>
            {analytics?.risk_score || 0}/100
          </h2>

          <p>
            {(analytics?.risk_score || 0) >= 70
              ? "🔴 High Risk"
              : (analytics?.risk_score || 0) >= 40
              ? "🟠 Medium Risk"
              : "🟢 Low Risk"}
          </p>
          {
            analytics?.risk_score >= 70 && (
              <p>
                High spending detected.
                Reduce non-essential expenses.
              </p>
            )
          }
        </div>
      </div>
      <div className="topbar-actions">

        <button
          onClick={onDownloadReport}
        >
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