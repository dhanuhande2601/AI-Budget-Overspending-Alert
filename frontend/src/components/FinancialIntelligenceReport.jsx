import { useEffect, useState } from 'react'
import {
  FiAlertTriangle,
  FiBarChart2,
  FiPieChart,
  FiTarget,
  FiTrendingUp,
} from 'react-icons/fi'
import { getFinancialReport } from '../api/budgetApi'

function formatINR(amount) {
  return `₹${Math.round(Number(amount || 0)).toLocaleString('en-IN')}`
}

const riskClass = {
  HIGH: 'danger-alert',
  MEDIUM: 'warning-alert',
  LOW: 'safe-alert',
}

export default function FinancialIntelligenceReport({ token }) {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) return
    let isCurrent = true

    getFinancialReport(token)
      .then((data) => {
        if (isCurrent) setReport(data)
      })
      .catch((err) => {
        if (isCurrent) setError(err.message)
      })
      .finally(() => {
        if (isCurrent) setLoading(false)
      })

    return () => { isCurrent = false }
  }, [token])

  if (loading) {
    return (
      <div className="panel">
        <p className="muted">Loading AI financial report...</p>
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="panel">
        <p className="muted">AI report isn't available right now. Try again shortly.</p>
      </div>
    )
  }

  const {
    projected_month_end_spending,
    projected_overspend,
    risk_level,
    daily_reduction_needed,
    top_categories = [],
    investment_suggestion = {},
  } = report

  return (
    <div className="panel">
      <div className="panel-heading">
        <div>
          <h2>🤖 AI Financial Intelligence Report</h2>
          <p className="panel-subtitle">
            Generated from your current spending pattern and projections
          </p>
        </div>
      </div>

      {/* Future Prediction */}
      <div className="section-block">
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
          <FiTrendingUp />
          <strong>Future Prediction</strong>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
          <span className="muted">Projected month-end spending</span>
          <strong>{formatINR(projected_month_end_spending)}</strong>
        </div>
        {projected_overspend > 0 && (
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span className="muted">Projected overspend</span>
            <strong style={{ color: '#b42318' }}>{formatINR(projected_overspend)}</strong>
          </div>
        )}
      </div>

      {/* Financial Risk */}
      <div className={riskClass[risk_level] || 'safe-alert'} style={{ marginTop: 14, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <FiAlertTriangle /> Financial Risk
        </span>
        <strong>{risk_level}</strong>
      </div>

      {/* Immediate Action */}
      {daily_reduction_needed > 0 && (
        <div className="warning-alert" style={{ marginTop: 10 }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
            <FiTarget /> Immediate Action
          </span>
          Reduce spending by <strong>{formatINR(daily_reduction_needed)}/day</strong> for the rest of the month
        </div>
      )}

      {/* Top Expense Categories */}
      {top_categories.length > 0 && (
        <div className="section-block">
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
            <FiBarChart2 />
            <strong>Top Expense Categories</strong>
          </div>
          {top_categories.map((item, index) => (
            <div key={item.category} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
              <span>{index + 1}. {item.category}</span>
              <strong>{formatINR(item.amount)}</strong>
            </div>
          ))}
        </div>
      )}

      {/* Investment Suggestion */}
      <div className="safe-alert" style={{ marginTop: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
          <FiPieChart /> Investment Suggestion
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
          <span>Current investable amount</span>
          <strong>
            {formatINR(investment_suggestion.min_amount)} – {formatINR(investment_suggestion.max_amount)}
          </strong>
        </div>
        {investment_suggestion.suggestions?.length > 0 && (
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {investment_suggestion.suggestions.map((tip) => (
              <span
                key={tip}
                style={{
                  fontSize: 12,
                  background: 'var(--card)',
                  padding: '4px 10px',
                  borderRadius: 999,
                }}
              >
                {tip}
              </span>
            ))}
          </div>
        )}
        <p className="muted" style={{ fontSize: 11, marginTop: 10, marginBottom: 0 }}>
          General informational suggestion, not personalized financial advice.
        </p>
      </div>
    </div>
  )
}