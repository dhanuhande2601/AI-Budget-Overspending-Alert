import { FiAlertTriangle } from 'react-icons/fi'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

function AlertsTrendSection({
  alerts = [],
  analytics = {},
  isBudgetExceeded,
  isBudgetWarning,
  trendData = [],
}) {
  const budgetAlerts = analytics?.budget_alerts || []

  return (
    <div className="panel">
      <h2>Overspending Alerts</h2>

      <div className="alert-list">
        {alerts.length ? (
          alerts.map((alert) => (
            <div className="alert-row" key={alert.category}>
              <FiAlertTriangle />
              <span>{alert.alert}</span>
            </div>
          ))
        ) : (
          <FallbackAlert
            isBudgetExceeded={isBudgetExceeded}
            isBudgetWarning={isBudgetWarning}
          />
        )}
      </div>

      {budgetAlerts.length > 0 && (
        <div className="section-block">
          <h2>Budget Usage Alerts</h2>

          <div className="alert-list">
            {budgetAlerts.map((alert) => (
              <div
                className="alert-row"
                key={`${alert.level}-${alert.message}`}
              >
                <FiAlertTriangle />
                <span>{alert.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="section-block">
        <h2>Monthly Spending Trend</h2>

        <div className="chart-frame">
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Legend />

              <Line
                type="monotone"
                dataKey="amount"
                stroke="#2f6fed"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

function FallbackAlert({
  isBudgetExceeded,
  isBudgetWarning,
}) {
  if (isBudgetExceeded) {
    return (
      <div className="alert-row">
        <FiAlertTriangle />
        <span>Budget limit exceeded</span>
      </div>
    )
  }

  if (isBudgetWarning) {
    return (
      <div className="alert-row">
        <FiAlertTriangle />
        <span>80% monthly budget used</span>
      </div>
    )
  }

  return <p className="muted">No overspending alerts.</p>
}

export default AlertsTrendSection