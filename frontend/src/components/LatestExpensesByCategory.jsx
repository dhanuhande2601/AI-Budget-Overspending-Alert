import { useState } from "react"

function LatestExpensesByCategory({
  data = [],
  alerts = []
}) {

  const [showAll, setShowAll] = useState(false)

  const expenses = Array.isArray(data)
    ? (
        showAll
          ? data
          : data.slice(0, 10)
      )
    : []

  const safeAlerts = Array.isArray(alerts)
    ? alerts
    : (alerts?.alerts || [])

  const alertMap = safeAlerts.reduce(
    (map, alert) => {

      if (alert.category) {
        map[alert.category.toLowerCase()] = alert
      }

      return map

    },
    {}
  )

  const getAlertLabel = (category) => {

    const alert =
      alertMap[(category || "").toLowerCase()]

    if (!alert) {
      return {
        label: "Safe",
        variant: "safe"
      }
    }

    if (
      alert.type === "exceeded" ||
      alert.level === "danger"
    ) {
      return {
        label: "Budget Exceeded",
        variant: "danger"
      }
    }

    if (
      alert.type === "critical" ||
      alert.level === "critical"
    ) {
      return {
        label: "Critical",
        variant: "danger"
      }
    }

    if (
      alert.type === "warning" ||
      alert.level === "warning"
    ) {
      return {
        label: "Budget Warning",
        variant: "warning"
      }
    }

    return {
      label: "Safe",
      variant: "safe"
    }
  }

  return (
    <div className="panel latest-expenses-panel">

      <div className="panel-heading">
        <div>
          <h2>
            Latest Expenses
          </h2>

          <p className="panel-subtitle">
            Quick expense pulse for recent spending and category alerts.
          </p>
        </div>
      </div>

      {expenses.length === 0 ? (

        <p>No recent expenses found.</p>

      ) : (

        <>
          <div className="table-wrapper">

            <table className="budget-table latest-expense-table">

              <thead>
                <tr>
                  <th className="text-left">
                    Category
                  </th>

                  <th className="text-left">
                    Description
                  </th>

                  <th>
                    Amount
                  </th>

                  <th>
                    Payment
                  </th>

                  <th>
                    Date & Time
                  </th>

                  <th>
                    Status
                  </th>
                </tr>
              </thead>

              <tbody>

                {expenses.map((expense) => {

                  const alert =
                    getAlertLabel(
                      expense.category
                    )

                  return (

                    <tr
                      key={
                        expense.id ||
                        `${expense.category}-${expense.title}-${expense.amount}`
                      }
                    >

                      <td className="text-left">
                        {expense.category || "N/A"}
                      </td>

                      <td className="text-left">
                        {expense.title}
                      </td>

                      <td>
                        ₹{Number(
                          expense.amount
                        ).toFixed(2)}
                      </td>

                      <td>
                        {expense.payment_method}
                      </td>

                      <td>
                        {expense.created_at
                          ? new Date(
                              expense.created_at
                            ).toLocaleString(
                              "en-IN",
                              {
                                timeZone: "Asia/Kolkata",
                                day: "2-digit",
                                month: "short",
                                year: "numeric",
                                hour: "2-digit",
                                minute: "2-digit",
                                hour12: true
                              }
                            )
                          : "N/A"}
                      </td>

                      <td>
                        <span
                          className={`status-badge ${alert.variant}`}
                        >
                          {alert.label}
                        </span>
                      </td>

                    </tr>

                  )
                })}

              </tbody>

            </table>

          </div>

          {data.length > 10 && (

            <div
              style={{
                textAlign: "center",
                marginTop: "20px"
              }}
            >

              <button
                type="button"
                onClick={() =>
                  setShowAll(!showAll)
                }
                style={{
                  padding: "10px 20px",
                  borderRadius: "8px",
                  border: "none",
                  background:
                    "#5b4df5",
                  color: "white",
                  cursor: "pointer",
                  fontWeight: "600"
                }}
              >
                {showAll
                  ? "▲ Show Less"
                  : "▼ Show More"}
              </button>

            </div>

          )}

        </>

      )}

    </div>
  )
}

export default LatestExpensesByCategory