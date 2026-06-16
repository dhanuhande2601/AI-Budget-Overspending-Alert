import {
  BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'

export default function CategoryPredictionsChart({ data }) {
  if (!data || !data.predictions) return null

  // Recharts ke liye data format karo
  const chartData = data.predictions.map((item) => ({
    name: item.category,
    Spent: Math.round(item.spent_so_far),
    Predicted: Math.round(item.predicted_total),
    Budget: Math.round(item.budget_limit || 0)
  }))

  return (
    <div className="bg-white rounded-2xl p-5 shadow mb-4">
      <h3 className="text-lg font-semibold mb-1">
        📊 Month-End Category Predictions
      </h3>
      <p className="text-sm text-gray-500 mb-4">
        Is mahine ke end tak kitna kharch hoga — category wise
      </p>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={chartData}
          margin={{ top: 10, right: 20, left: 0, bottom: 60 }}
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
          <Tooltip formatter={(val) => `₹${val}`} />
          <Legend verticalAlign="top" />
          <Bar dataKey="Spent" fill="#60a5fa" radius={[4,4,0,0]} />
          <Bar dataKey="Predicted" fill="#f97316" radius={[4,4,0,0]} />
          <Bar dataKey="Budget" fill="#4ade80" radius={[4,4,0,0]} />
        </BarChart>
      </ResponsiveContainer>

      {/* Warning list */}
      {data.predictions.filter(p => p.predicted_total > p.budget_limit).length > 0 && (
        <div className="mt-4 bg-red-50 rounded-xl p-3">
          <p className="text-sm font-semibold text-red-600 mb-2">
            ⚠️ In categories me overspend ho sakta hai:
          </p>
          {data.predictions
            .filter(p => p.predicted_total > p.budget_limit)
            .map((p, i) => (
              <p key={i} className="text-sm text-red-500">
                • {p.category} — Predicted ₹{Math.round(p.predicted_total)},
                Budget ₹{Math.round(p.budget_limit)}
              </p>
            ))}
        </div>
      )}
    </div>
  )
}