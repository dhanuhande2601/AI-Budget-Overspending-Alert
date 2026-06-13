import { FiAlertTriangle, FiBarChart2, FiUser } from 'react-icons/fi'

function Metrics({
  alertCount = 0,
  analytics = {},
  isBudgetExceeded = false,
  isBudgetWarning,
  monthlyBudget = 0,
  totalSpending = 0,
}) {
  const safeTotalSpending = Number(totalSpending) || 0
  const safeMonthlyBudget = Number(monthlyBudget) || 0
  const safePredictedSpending =
    Number(analytics?.predicted_spending) || 0

  return (
    <section className="metrics">
      <div className="metric-card">
        <FiBarChart2 aria-hidden="true" />
        <span>Total spending</span>
        <strong>Rs. {safeTotalSpending.toFixed(2)}</strong>
      </div>

      <div className="metric-card">
        <FiUser aria-hidden="true" />
        <span>Monthly budget</span>
        <strong>Rs. {safeMonthlyBudget.toFixed(2)}</strong>
      </div>

      <div className="metric-card">
        <FiBarChart2 aria-hidden="true" />
        <span>Predicted month-end spending</span>
        <strong>Rs. {safePredictedSpending.toFixed(2)}</strong>
      </div>

      <div className="metric-card">
        <FiAlertTriangle aria-hidden="true" />
        <span>Alerts</span>
        <strong>{Number(alertCount) || 0}</strong>

        {isBudgetExceeded ? (
          <div className="danger-alert">
            🚨 Budget Exceeded
          </div>
        ) : isBudgetWarning ? (
          <div className="warning-alert">
            ⚠️ Budget Near Limit
          </div>
        ) : (
          <div className="safe-alert">
             Within Budget
          </div>
        )}
      </div>
    </section>
  )
}

export default Metrics