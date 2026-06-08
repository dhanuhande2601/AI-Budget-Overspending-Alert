const DashboardTable = ({ data }) => {
  return (
    <div className="dashboard-table">
      <table>
        <thead>
          <tr>
            <th>Category</th>
            <th>Total Expense</th>
            <th>Recent Items</th>
            <th>Budget</th>
            <th>Status</th>
            <th>Alerts</th>
          </tr>
        </thead>

        <tbody>
          {data.map((item, index) => (
            <tr key={index}>
              
              {/* Category */}
              <td>{item.category}</td>

              {/* Total Expense */}
              <td>₹{item.total}</td>

              {/* Recent Expenses */}
              <td>
                {item.recent.map((r, i) => (
                  <div key={i}>
                    {r.name} - ₹{r.amount}
                  </div>
                ))}
              </td>

              {/* Budget */}
              <td>₹{item.budget || 0}</td>

              {/* Status */}
              <td>
                {item.total > item.budget ? (
                  <span style={{ color: "red" }}>Over</span>
                ) : (
                  <span style={{ color: "green" }}>OK</span>
                )}
              </td>

              {/* Alerts */}
              <td>
                {item.alerts?.length ? (
                  item.alerts.map((a, i) => <div key={i}>{a}</div>)
                ) : (
                  "No alerts"
                )}
              </td>

            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DashboardTable;