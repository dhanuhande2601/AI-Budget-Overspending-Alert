import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

export default function CategoryPredictionsChart({ data }) {
  if (!data || !data.predictions) return null

  const chartData = data.predictions.map((item) => ({
    name: item.category,
    Spent: Math.round(item.spent_so_far),
    Predicted: Math.round(item.predicted_total),
    Budget: Math.round(item.budget_limit || 0),
  }))

  const overspendingPredictions = data.predictions.filter(
    (item) => item.predicted_total > item.budget_limit
  )

  return (
    <div className="panel">
      <div className="panel-heading compact">
        <div>
          <h2>Month-End Predictions</h2>
          <p className="panel-subtitle">Projected category usage against configured limits.</p>
        </div>
      </div>

      <div className="chart-frame tall">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 10, right: 12, left: 0, bottom: 64 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="name"
              angle={-35}
              textAnchor="end"
              interval={0}
              tick={{ fontSize: 11 }}
            />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip formatter={(val) => `Rs. ${Number(val).toLocaleString()}`} />
            <Legend verticalAlign="top" />
            <Bar dataKey="Spent" fill="#2563eb" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Predicted" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Budget" fill="#059669" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {overspendingPredictions.length > 0 && (
        <div className="alert-list section-block">
          <p className="summary-title">Projected overspend</p>
          {overspendingPredictions.map((item) => (
            <div className="alert-row" key={item.category}>
              <div>
                <strong>{item.category}</strong>
                <p>
                  Predicted Rs. {Math.round(item.predicted_total).toLocaleString()} against
                  budget Rs. {Math.round(item.budget_limit).toLocaleString()}.
                </p>
              </div>
              <span className="status-badge danger">Risk</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
