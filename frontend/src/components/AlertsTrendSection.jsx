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
  PieChart,
  Pie,
  Cell,
} from 'recharts'

const COLORS = [
  '#0088FE',
  '#00C49F',
  '#FFBB28',
  '#FF8042',
  '#AA00FF',
]

function AlertsTrendSection({
  alerts = [],
  analytics = {},
  isBudgetExceeded,
  isBudgetWarning,
  trendData = [],
}) {
  console.log("ALERTS =", alerts)
  console.log("ANALYTICS =", analytics)
  const budgetAlerts = analytics?.budget_alerts || []
  const pieData = analytics?.category_summary || []

  return (
    <div className="panel">
      <h2>Overspending Alerts</h2>

      <div className="alert-list">
        {alerts.length ? (
          alerts.map((alert, index) => (
            <div
              className="alert-row"
              key={`${alert.category}-${index}`}
            >
              <FiAlertTriangle />

              <div>
                <strong>{alert.category}</strong>

                <p>
                  {alert.message || alert.alert}
                </p>

                {alert.ai_recommendation && (
                  <p
                    style={{
                      color: '#2f6fed',
                      marginTop: '6px',
                    }}
                  >
                    🤖 {alert.ai_recommendation}
                  </p>
                )}
              </div>
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

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '20px',
          marginTop: '20px',
        }}
      >
        {/* PIE CHART */}

        {pieData.length > 0 && (
          <div className="section-block">
            <h2>Category Wise Spending</h2>

            <div className="chart-frame">
              <ResponsiveContainer
                width="100%"
                height={220}
              >
                <PieChart>
                  <Pie
                    data={pieData}
                    dataKey="amount"
                    nameKey="category"
                    cx="50%"
                    cy="50%"
                    outerRadius={70}
                    label
                  >
                    {pieData.map((entry, index) => (
                      <Cell
                        key={entry.category}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>

                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* MONTHLY TREND */}

        <div className="section-block">
          <h2>Monthly Spending Trend</h2>

          <div className="chart-frame">
            <ResponsiveContainer
              width="100%"
              height={220}
            >
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" />

                <XAxis dataKey="month" />

                <YAxis />

                <Tooltip />

                <Legend />

                <Line
                  type="monotone"
                  dataKey="amount"
                  name="Spending"
                  stroke="#2f6fed"
                  strokeWidth={3}
                  dot={{ r: 5 }}
                  activeDot={{ r: 8 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      <div className="section-block">
        
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

  return (
    <p className="muted">
      No overspending alerts.
    </p>
  )
}

export default AlertsTrendSection