import { useState } from 'react'
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
  weeklyTrendData = [],
}) {
  const [trendView, setTrendView] = useState('monthly')

  const budgetAlerts = analytics?.budget_alerts || []
  const pieData = analytics?.category_summary || []

  const activeData = trendView === 'monthly' ? trendData : weeklyTrendData
  const xAxisKey = trendView === 'monthly' ? 'month' : 'week'

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

        {/* SPENDING TREND — MONTHLY / WEEKLY TOGGLE */}

        <div className="section-block">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2>
              {trendView === 'monthly' ? 'Monthly' : 'Weekly'} Spending Trend
            </h2>
            <div style={{ display: 'flex', gap: 6 }}>
              <button
                type="button"
                className={trendView === 'monthly' ? '' : 'secondary-button'}
                style={{ minHeight: 32, padding: '6px 12px', fontSize: 12 }}
                onClick={() => setTrendView('monthly')}
              >
                Monthly
              </button>
              <button
                type="button"
                className={trendView === 'weekly' ? '' : 'secondary-button'}
                style={{ minHeight: 32, padding: '6px 12px', fontSize: 12 }}
                onClick={() => setTrendView('weekly')}
              >
                Weekly
              </button>
            </div>
          </div>

          <div className="chart-frame">
            {activeData.length === 0 ? (
              <p className="muted" style={{ marginTop: 20 }}>
                Not enough data yet for a {trendView} view.
              </p>
            ) : (
              <ResponsiveContainer
                width="100%"
                height={220}
              >
                <LineChart data={activeData}>
                  <CartesianGrid strokeDasharray="3 3" />

                  <XAxis dataKey={xAxisKey} tick={{ fontSize: 11 }} />

                  <YAxis tick={{ fontSize: 11 }} />

                  <Tooltip formatter={(val) => `₹${val.toLocaleString()}`} />

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
            )}
          </div>
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

  return (
    <p className="muted">
      No overspending alerts.
    </p>
  )
}

export default AlertsTrendSection
