import { useState } from 'react'
import { FiAlertTriangle } from 'react-icons/fi'

import {
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const COLORS = [
  '#2563eb',
  '#0f9f9c',
  '#f59e0b',
  '#ef4444',
  '#64748b',
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
      <div className="panel-heading">
        <div>
          <h2>Overspending Monitor</h2>
          <p className="panel-subtitle">Alerts, category mix, and spending movement in one view.</p>
        </div>
      </div>

      <div className="alert-list">
        {alerts.length ? (
          alerts.map((alert, index) => (
            <div className="alert-row" key={`${alert.category}-${index}`}>
              <FiAlertTriangle aria-hidden="true" />

              <div>
                <strong>{alert.category || 'Budget'}</strong>
                <p>{alert.message || alert.alert}</p>

                {alert.ai_recommendation && (
                  <p className="ai-note">{alert.ai_recommendation}</p>
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
              <div className="alert-row" key={`${alert.level}-${alert.message}`}>
                <FiAlertTriangle aria-hidden="true" />
                <span>{alert.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="analytics-grid">
        {pieData.length > 0 && (
          <div className="section-block chart-section">
            <h2>Category Spending Mix</h2>

            <div className="chart-frame">
              <ResponsiveContainer width="100%" height="100%">
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
                      <Cell key={entry.category} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>

                  <Tooltip formatter={(val) => `Rs. ${Number(val).toLocaleString()}`} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        <div className="section-block chart-section">
          <div className="chart-heading">
            <h2>{trendView === 'monthly' ? 'Monthly' : 'Weekly'} Spending Trend</h2>
            <div className="segmented-control">
              <button
                type="button"
                className={trendView === 'monthly' ? 'active' : ''}
                onClick={() => setTrendView('monthly')}
              >
                Monthly
              </button>
              <button
                type="button"
                className={trendView === 'weekly' ? 'active' : ''}
                onClick={() => setTrendView('weekly')}
              >
                Weekly
              </button>
            </div>
          </div>

          <div className="chart-frame">
            {activeData.length === 0 ? (
              <p className="muted">Not enough data yet for a {trendView} view.</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={activeData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey={xAxisKey} tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(val) => `Rs. ${Number(val).toLocaleString()}`} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="amount"
                    name="Spending"
                    stroke="#2563eb"
                    strokeWidth={3}
                    dot={{ r: 4 }}
                    activeDot={{ r: 6 }}
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

function FallbackAlert({ isBudgetExceeded, isBudgetWarning }) {
  if (isBudgetExceeded) {
    return (
      <div className="alert-row">
        <FiAlertTriangle aria-hidden="true" />
        <span>Budget limit exceeded</span>
      </div>
    )
  }

  if (isBudgetWarning) {
    return (
      <div className="alert-row">
        <FiAlertTriangle aria-hidden="true" />
        <span>80% monthly budget used</span>
      </div>
    )
  }

  return <p className="muted">No overspending alerts.</p>
}

export default AlertsTrendSection
