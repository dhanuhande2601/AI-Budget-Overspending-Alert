import { FiAlertTriangle, FiBarChart2, FiTarget, FiTrendingUp } from 'react-icons/fi'

function Metrics({
  alertCount = 0,
  analytics = {},
  formatAmount,
  isBudgetExceeded = false,
  isBudgetWarning,
  monthlyBudget = 0,
  totalSpending = 0,
}) {
  const safeTotalSpending = Number(totalSpending) || 0
  const safeMonthlyBudget = Number(monthlyBudget) || 0
  const safePredictedSpending = Number(analytics?.predicted_spending) || 0
  const money = formatAmount || ((amt) => `Rs. ${Number(amt || 0).toFixed(2)}`)

  return (
    <section className="metrics">
      <div className="metric-card">
        <FiBarChart2 aria-hidden="true" />
        <span>Total spending</span>
        <strong>{money(safeTotalSpending)}</strong>
      </div>

      <div className="metric-card">
        <FiTarget aria-hidden="true" />
        <span>Monthly budget</span>
        <strong>{money(safeMonthlyBudget)}</strong>
      </div>

      <div className="metric-card">
        <FiTrendingUp aria-hidden="true" />
        <span>Predicted month-end</span>
        <strong>{money(safePredictedSpending)}</strong>
      </div>

      <div className="metric-card">
        <FiAlertTriangle aria-hidden="true" />
        <span>Active alerts</span>
        <strong>{Number(alertCount) || 0}</strong>

        {isBudgetExceeded ? (
          <div className="danger-alert">Budget exceeded</div>
        ) : isBudgetWarning ? (
          <div className="warning-alert">Budget near limit</div>
        ) : (
          <div className="safe-alert">Within budget</div>
        )}
      </div>
    </section>
  )
}

export default Metrics
