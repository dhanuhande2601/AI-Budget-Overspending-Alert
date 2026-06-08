import { FiAlertTriangle, FiBarChart2, FiUser } from 'react-icons/fi'

function Metrics({
  alertCount,
  analytics,
  isBudgetExceeded,
  isBudgetWarning,
  monthlyBudget,
  totalSpending,
}) {
  return (
    <section className="metrics">
      <div className="metric-card">
        <FiBarChart2 aria-hidden="true" />
        <span>Total spending</span>
        <strong>Rs. {totalSpending.toFixed(2)}</strong>
      </div>

      <div className="metric-card">
        <FiUser aria-hidden="true" />
        <span>Monthly budget</span>
        <strong>Rs. {monthlyBudget.toFixed(2)}</strong>
      </div>

      <div className="metric-card">
        <FiBarChart2 aria-hidden="true" />
        <span>Predicted month-end spending</span>
        <strong>Rs. {Number(analytics.predicted_spending || 0).toFixed(2)}</strong>
      </div>

      <div className="metric-card">
        <FiAlertTriangle aria-hidden="true" />
        <span>Alerts</span>
        <strong>{alertCount}</strong>
        {isBudgetExceeded ? (
          <div className="danger-alert">Budget limit exceeded</div>
        ) : isBudgetWarning ? (
          <div className="warning-alert">80% budget used</div>
        ) : (
          <div className="safe-alert">Budget under control</div>
        )}
      </div>
    </section>
  )
}

export default Metrics
