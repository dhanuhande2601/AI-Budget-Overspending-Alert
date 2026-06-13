function CategoryBudgetTable({ budgets = [] }) {
  if (!budgets.length) {
    return (
      <div className="panel">
        <h2>Category Budget Status</h2>
        <p>No category budgets found.</p>
      </div>
    )
  }

  return (
    <div className="panel">
      <h2>Category Budget Status</h2>

      <div className="table-wrapper">
        <table className="budget-table">
          <thead>
            <tr>
              <th>Category</th>
              <th>Budget</th>
              <th>Spent</th>
              <th>Remaining</th>
              <th>Usage</th>
              <th>Status</th>
            </tr>
          </thead>

          <tbody>
            {budgets.map((item) => {
              const budget = Number(
                item.budget ||
                item.monthly_limit ||
                0
              )

              const spent = Number(
                item.spent || 0
              )

              const remaining = Math.max(
                budget - spent,
                0
              )

              const percent =
                budget > 0
                  ? Math.round(
                      (spent / budget) * 100
                    )
                  : 0

              let status = 'Safe'
              let statusClass = 'safe'

              if (percent >= 80) {
                status = 'Warning'
                statusClass = 'warning'
              }

              if (percent >= 100) {
                status = 'Exceeded'
                statusClass = 'danger'
              }

              return (
                <tr key={item.category}>
                  <td>
                    <strong>
                      {item.category}
                    </strong>
                  </td>

                  <td>
                    ₹{budget.toFixed(2)}
                  </td>

                  <td>
                    ₹{spent.toFixed(2)}
                  </td>

                  <td>
                    ₹{remaining.toFixed(2)}
                  </td>

                  <td>
                    <div className="progress-container">
                      <div
                        className={`progress-bar ${statusClass}`}
                        style={{
                          width: `${Math.min(
                            percent,
                            100
                          )}%`,
                        }}
                      />
                    </div>

                    <small>
                      {percent}%
                    </small>
                  </td>

                  <td>
                    <span
                      className={`status-badge ${statusClass}`}
                    >
                      {status}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default CategoryBudgetTable