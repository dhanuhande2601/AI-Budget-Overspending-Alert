function MonthlyInsights({ data }) {
  if (!data) return null

  return (
    <div className="card">
      <h2>📊 Monthly Insights</h2>

      <p>
        <strong>Highest Category:</strong>
        {data.highest_category}
        (₹{Number(data.highest_amount || 0).toFixed(2)})
      </p>

      <p>
        <strong>Lowest Category:</strong>
        {data.lowest_category}
        (₹{Number(data.lowest_amount || 0).toFixed(2)})
      </p>

      <p>
        <strong>Transactions:</strong>
        {data.total_transactions || 0}
      </p>

      <p>
        <strong>Average Expense:</strong>
        ₹{Number(data.average_expense || 0).toFixed(2)}
      </p>

      <p>
        <strong>Total Spending:</strong>
        ₹{Number(data.total_spending || 0).toFixed(2)}
      </p>

      <hr />

      <div
        style={{
          background: "#eef6ff",
          padding: "12px",
          borderRadius: "8px",
          marginTop: "10px",
        }}
      >
        <h3>🤖 AI Recommendation</h3>

        <p
          style={{
            whiteSpace: "normal",
            wordBreak: "break-word",
            overflowWrap: "break-word",
            lineHeight: "1.8",
            width: "100%",
          }}
        >
          {data.ai_recommendation || "No recommendation available"}
        </p>
      </div>
    </div>
  )
}

export default MonthlyInsights