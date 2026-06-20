import { useEffect, useState } from 'react'
import {
  FiAlertTriangle,
  FiPieChart,
  FiTarget,
  FiZap,
} from 'react-icons/fi'
import { getFinancialReport, getMonthlyInsights } from '../api/budgetApi'

function formatINR(amount) {
  return `₹${Math.round(Number(amount || 0)).toLocaleString('en-IN')}`
}

const RISK_CONFIG = {
  HIGH:   { label: 'High',   percent: 90, badgeClass: 'danger-alert' },
  MEDIUM: { label: 'Medium', percent: 55, badgeClass: 'warning-alert' },
  LOW:    { label: 'Low',    percent: 20, badgeClass: 'safe-alert' },
}

export default function FinancialIntelligenceReport({ token }) {
  const [report, setReport] = useState(null)
  const [insights, setInsights] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token) return
    let isCurrent = true

    Promise.all([
      getFinancialReport(token),
      getMonthlyInsights(token).catch(() => null), // non-critical, don't fail the whole panel
    ])
      .then(([reportData, insightsData]) => {
        if (!isCurrent) return
        setReport(reportData)
        setInsights(insightsData)
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

  const risk = RISK_CONFIG[risk_level] || RISK_CONFIG.LOW
  const maxCategoryAmount = top_categories[0]?.amount || 0
  const hasInsights = insights && !insights.message // backend sends {message: "No expenses found"} when empty

  return (
    <div className="panel">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div
            style={{
              width: 36, height: 36, borderRadius: '50%',
              background: 'var(--input-bg)', display: 'flex',
              alignItems: 'center', justifyContent: 'center',
            }}
          >
            <FiZap size={18} />
          </div>
          <h2 style={{ margin: 0 }}>AI financial report</h2>
        </div>
        <span style={{ fontSize: 11, color: 'var(--muted)' }}>Updated today</span>
      </div>

      {/* Monthly stats strip — merged in from the old standalone Monthly Insights panel */}
      {hasInsights && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: 10,
            marginBottom: 16,
            paddingBottom: 16,
            borderBottom: '1px solid var(--soft-border)',
          }}
        >
          <div>
            <p style={{ fontSize: 11, color: 'var(--muted)', margin: '0 0 2px' }}>Highest category</p>
            <p style={{ fontSize: 14, fontWeight: 500, margin: 0 }}>
              {insights.highest_category} <span style={{ color: 'var(--muted)', fontWeight: 400 }}>({formatINR(insights.highest_amount)})</span>
            </p>
          </div>
          <div>
            <p style={{ fontSize: 11, color: 'var(--muted)', margin: '0 0 2px' }}>Lowest category</p>
            <p style={{ fontSize: 14, fontWeight: 500, margin: 0 }}>
              {insights.lowest_category} <span style={{ color: 'var(--muted)', fontWeight: 400 }}>({formatINR(insights.lowest_amount)})</span>
            </p>
          </div>
          <div>
            <p style={{ fontSize: 11, color: 'var(--muted)', margin: '0 0 2px' }}>Transactions</p>
            <p style={{ fontSize: 14, fontWeight: 500, margin: 0 }}>{insights.total_transactions || 0}</p>
          </div>
          <div>
            <p style={{ fontSize: 11, color: 'var(--muted)', margin: '0 0 2px' }}>Average expense</p>
            <p style={{ fontSize: 14, fontWeight: 500, margin: 0 }}>{formatINR(insights.average_expense)}</p>
          </div>
        </div>
      )}

      {/* Two metric cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
        <div style={{ background: 'var(--input-bg)', borderRadius: 10, padding: 12 }}>
          <p style={{ fontSize: 12, color: 'var(--muted)', margin: '0 0 4px' }}>Projected month-end</p>
          <p style={{ fontSize: 20, fontWeight: 500, margin: 0 }}>{formatINR(projected_month_end_spending)}</p>
        </div>
        <div className={projected_overspend > 0 ? 'danger-alert' : 'safe-alert'} style={{ borderRadius: 10, padding: 12 }}>
          <p style={{ fontSize: 12, margin: '0 0 4px' }}>Projected overspend</p>
          <p style={{ fontSize: 20, fontWeight: 500, margin: 0 }}>
            {projected_overspend > 0 ? formatINR(projected_overspend) : 'None'}
          </p>
        </div>
      </div>

      {/* Risk level with bar */}
      <div
        className={risk.badgeClass}
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '10px 12px', borderRadius: 10, marginBottom: 10,
        }}
      >
        <span style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}>
          <FiAlertTriangle size={15} /> Risk level
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ width: 70, height: 6, borderRadius: 3, background: 'var(--card)', overflow: 'hidden' }}>
            <div style={{ width: `${risk.percent}%`, height: '100%', background: 'currentColor' }} />
          </div>
          <span style={{ fontSize: 13, fontWeight: 500 }}>{risk.label}</span>
        </div>
      </div>

      {/* Immediate action */}
      {daily_reduction_needed > 0 && (
        <div style={{ borderRadius: 10, border: '1px solid var(--soft-border)', padding: 12, marginBottom: 16 }}>
          <p style={{ fontSize: 13, margin: 0, display: 'flex', alignItems: 'flex-start', gap: 8 }}>
            <FiTarget size={16} style={{ marginTop: 1, color: 'var(--muted)', flexShrink: 0 }} />
            <span>
              To stay on track, cut spending by{' '}
              <strong>{formatINR(daily_reduction_needed)}/day</strong> for the rest of this month.
            </span>
          </p>
        </div>
      )}

      {/* Top categories with bars */}
      {top_categories.length > 0 && (
        <>
          <p style={{ fontSize: 12, color: 'var(--muted)', margin: '0 0 8px', textTransform: 'uppercase', letterSpacing: '0.02em' }}>
            Top categories
          </p>
          <div style={{ marginBottom: 16 }}>
            {top_categories.map((item) => (
              <div key={item.category} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                <span style={{ fontSize: 13, width: 70, flexShrink: 0 }}>{item.category}</span>
                <div style={{ flex: 1, height: 6, borderRadius: 3, background: 'var(--input-bg)', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${maxCategoryAmount > 0 ? (item.amount / maxCategoryAmount) * 100 : 0}%`,
                      height: '100%',
                      background: 'var(--muted)',
                    }}
                  />
                </div>
                <span style={{ fontSize: 13, fontWeight: 500, width: 70, textAlign: 'right' }}>
                  {formatINR(item.amount)}
                </span>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Investment suggestion */}
      <div className="safe-alert" style={{ borderRadius: 10, padding: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
          <FiPieChart size={15} />
          <span style={{ fontSize: 13, fontWeight: 500 }}>Investable this month</span>
        </div>
        <p style={{ fontSize: 19, fontWeight: 500, margin: '0 0 10px' }}>
          {formatINR(investment_suggestion.min_amount)} – {formatINR(investment_suggestion.max_amount)}
        </p>
        {investment_suggestion.suggestions?.length > 0 && (
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>
            {investment_suggestion.suggestions.map((tip) => (
              <span
                key={tip}
                style={{ fontSize: 12, background: 'var(--card)', padding: '4px 10px', borderRadius: 999 }}
              >
                {tip}
              </span>
            ))}
          </div>
        )}
        <p style={{ fontSize: 11, color: 'var(--muted)', margin: 0 }}>
          General informational suggestion, not personalized financial advice.
        </p>
      </div>
    </div>
  )
}