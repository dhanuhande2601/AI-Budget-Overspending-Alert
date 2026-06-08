import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'

const COLORS = [
  '#0088FE',
  '#00C49F',
  '#FFBB28',
  '#FF8042',
  '#AA00FF',
]

function AnalyticsSection({ analytics = {} }) {
  const data = analytics.category_summary || []

  return (
    <>
      <div className="panel">
        <h2>Category Analytics</h2>

        <div className="expense-list">
          {data.map((item) => (
            <div
              className="expense-row"
              key={item.category}
            >
              <strong>{item.category}</strong>

              <b>
                ₹{Number(item.amount).toFixed(2)}
              </b>
            </div>
          ))}
        </div>
      </div>

      <div className="panel">
        <h2>Expense Analytics Chart</h2>

        <div className="chart-frame">
          <ResponsiveContainer
            width="100%"
            height={250}
          >
            <PieChart>
              <Pie
                data={data}
                dataKey="amount"
                nameKey="category"
                outerRadius={90}
                label
              >
                {data.map((entry, index) => (
                  <Cell
                    key={entry.category}
                    fill={
                      COLORS[
                        index % COLORS.length
                      ]
                    }
                  />
                ))}
              </Pie>

              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </>
  )
}

export default AnalyticsSection