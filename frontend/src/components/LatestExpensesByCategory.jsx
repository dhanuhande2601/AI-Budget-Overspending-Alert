import { useState } from 'react'
import { FiChevronDown, FiChevronUp } from 'react-icons/fi'

function LatestExpensesByCategory({ data = [], alerts = [] }) {
  const [showAll, setShowAll] = useState(false)

  const sortedExpenses = Array.isArray(data)
    ? [...data].sort((a, b) => {
        const bTime = new Date(b.created_at || 0).getTime()
        const aTime = new Date(a.created_at || 0).getTime()
        if (bTime !== aTime) return bTime - aTime
        return Number(b.id || 0) - Number(a.id || 0)
      })
    : []

  const expenses = showAll ? sortedExpenses : sortedExpenses.slice(0, 10)
  const hasMoreExpenses = sortedExpenses.length > 10

  const safeAlerts = Array.isArray(alerts) ? alerts : (alerts?.alerts || [])

  const alertMap = safeAlerts.reduce((map, alert) => {
    if (alert.category) {
      map[alert.category.toLowerCase()] = alert
    }
    return map
  }, {})

  const getAlertLabel = (category) => {
    const alert = alertMap[(category || '').toLowerCase()]

    if (!alert) {
      return { label: 'Safe', variant: 'safe' }
    }

    if (alert.type === 'exceeded' || alert.level === 'danger') {
      return { label: 'Exceeded', variant: 'danger' }
    }

    if (alert.type === 'critical' || alert.level === 'critical') {
      return { label: 'Critical', variant: 'danger' }
    }

    if (alert.type === 'warning' || alert.level === 'warning') {
      return { label: 'Warning', variant: 'warning' }
    }

    return { label: 'Safe', variant: 'safe' }
  }

  const formatExpenseDate = (dateValue) => {
    if (!dateValue) return 'N/A'

    return new Date(dateValue).toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    })
  }

  return (
    <div className="panel latest-expenses-panel">
      <div className="panel-heading compact">
        <div>
          <h2>Latest Expenses</h2>
          <p className="panel-subtitle">Recent spending with category alert status.</p>
        </div>
      </div>

      {expenses.length === 0 ? (
        <p className="muted">No recent expenses found.</p>
      ) : (
        <div className="table-wrapper latest-expense-wrapper">
          <table className="budget-table latest-expense-table">
            <colgroup>
              <col className="latest-col-category" />
              <col className="latest-col-description" />
              <col className="latest-col-amount" />
              <col className="latest-col-payment" />
              <col className="latest-col-date" />
              <col className="latest-col-status" />
            </colgroup>
            <thead>
              <tr>
                <th className="text-left">Category</th>
                <th className="text-left">Description</th>
                <th>Amount</th>
                <th>Payment</th>
                <th>Date & Time</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {expenses.map((expense) => {
                const alert = getAlertLabel(expense.category)

                return (
                  <tr
                    key={
                      expense.id ||
                      `${expense.category}-${expense.title}-${expense.amount}`
                    }
                  >
                    <td className="text-left">{expense.category || 'N/A'}</td>
                    <td className="text-left latest-description">
                      {expense.title || 'Untitled expense'}
                    </td>
                    <td className="latest-amount">Rs. {Number(expense.amount || 0).toFixed(2)}</td>
                    <td className="latest-payment">{expense.payment_method || '-'}</td>
                    <td className="latest-date">{formatExpenseDate(expense.created_at)}</td>
                    <td className="latest-status">
                      <span className={`status-badge ${alert.variant}`}>
                        {alert.label}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>

          {hasMoreExpenses && (
            <div className="latest-expense-toggle-row">
              <button
                className="latest-expense-toggle"
                type="button"
                onClick={() => setShowAll((current) => !current)}
                aria-label={showAll ? 'Show latest 10 expenses' : 'Show all expenses'}
              >
                {showAll ? <FiChevronUp aria-hidden="true" /> : <FiChevronDown aria-hidden="true" />}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default LatestExpensesByCategory
