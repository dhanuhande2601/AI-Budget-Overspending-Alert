function LatestExpensesByCategory({ data = [], alerts = [] }) {
  const expenses = Array.isArray(data) ? data.slice(0, 10) : []

  const alertMap = alerts.reduce((map, alert) => {
    if (alert.category) {
      map[alert.category] = alert
    }
    return map
  }, {})

  const getAlertLabel = (category) => {
    const alert = alertMap[category]
    if (!alert) return { label: 'Safe', variant: 'safe' }
    if (alert.type === 'exceeded') return { label: 'Budget Exceeded', variant: 'danger' }
    if (alert.type === 'warning') return { label: 'Budget Warning', variant: 'warning' }
    return { label: 'Safe', variant: 'safe' }
  }

  return (
    <div className="panel latest-expenses-panel">
      <div className="panel-heading">
        <div>
          <h2>Latest 10 Expenses</h2>
          <p className="panel-subtitle">Quick expense pulse for recent spending and category alerts.</p>
        </div>
      </div>

      {expenses.length === 0 ? (
        <p>No recent expenses found.</p>
      ) : (
        <div className="table-wrapper">
          <table className="budget-table latest-expense-table">
            <thead>
              <tr>
                <th className="text-left">Category</th>
                <th className="text-left">Description</th>
                <th>Amount</th>
                <th>Payment</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {expenses.map((expense) => {
                const alert = getAlertLabel(expense.category)
                return (
                  <tr key={expense.id || `${expense.category}-${expense.title}-${expense.amount}`}>
                    <td className="text-left">{expense.category || 'Uncategorized'}</td>
                    <td className="text-left">{expense.title}</td>
                    <td>₹{Number(expense.amount).toFixed(2)}</td>
                    <td>{expense.payment_method || '-'}</td>
                    <td>
                      <span className={`status-badge ${alert.variant}`}>{alert.label}</span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default LatestExpensesByCategory