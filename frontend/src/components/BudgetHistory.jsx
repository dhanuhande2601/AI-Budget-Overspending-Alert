import { useEffect, useState } from 'react'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import { FiTrendingDown, FiTrendingUp, FiCalendar } from 'react-icons/fi'
import { getBudgetHistory, getBudgetHistorySummary, saveBudgetSnapshot } from '../api/budgetApi'

export default function BudgetHistory({ token }) {
  const [history, setHistory] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [chartType, setChartType] = useState('bar')

  useEffect(() => {
    loadData()
  }, [token])

  async function loadData() {
    setLoading(true)
    try {
      const [historyData, summaryData] = await Promise.all([
        getBudgetHistory(token),
        getBudgetHistorySummary(token),
      ])
      setHistory(Array.isArray(historyData) ? historyData : [])
      setSummary(summaryData)
    } catch (error) {
      console.log('Budget history load error:', error)
    }
    setLoading(false)
  }

  async function handleSaveSnapshot() {
    try {
      await saveBudgetSnapshot(token)
      await loadData()
    } catch (error) {
      console.log(error)
    }
  }

  if (loading) {
    return (
      <div className="panel">
        <p className="muted">Loading budget history...</p>
      </div>
    )
  }

  if (!history.length) {
    return (
      <div className="panel">
        <div className="panel-heading">
          <div>
            <h2>📅 Budget History</h2>
            <p className="panel-subtitle">Month-wise budget tracking</p>
          </div>
        </div>
        <p className="muted">No history yet. Snapshots save automatically at month end.</p>
        <button onClick={handleSaveSnapshot} style={{ marginTop: 12 }}>
          Save Current Month Snapshot
        </button>
      </div>
    )
  }

  const chartData = [...summary.chart_data].reverse()

  return (
    <div className="panel">
      <div className="panel-heading">
        <div>
          <h2>📅 Budget History</h2>
          <p className="panel-subtitle">Track how your spending changed month by month</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            className={chartType === 'bar' ? '' : 'secondary-button'}
            onClick={() => setChartType('bar')}
          >
            Bar
          </button>
          <button
            className={chartType === 'line' ? '' : 'secondary-button'}
            onClick={() => setChartType('line')}
          >
            Line
          </button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="metrics" style={{ marginBottom: 18 }}>
        <div className="metric-card">
          <span>Avg Monthly Spent</span>
          <strong>₹{summary.avg_spent.toLocaleString()}</strong>
        </div>
        <div className="metric-card">
          <span>Avg Monthly Saved</span>
          <strong>₹{summary.avg_saved.toLocaleString()}</strong>
        </div>
        <div className="metric-card">
          <span><FiTrendingDown style={{ color: '#16a34a' }} /> Best Month</span>
          <strong>{summary.best_month}</strong>
        </div>
        <div className="metric-card">
          <span><FiTrendingUp style={{ color: '#b42318' }} /> Overspent Months</span>
          <strong>{summary.overspent_months} / {summary.total_months}</strong>
        </div>
      </div>

      {/* Chart */}
      <div className="chart-frame" style={{ height: 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          {chartType === 'bar' ? (
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month_label" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip formatter={(val) => `₹${val.toLocaleString()}`} />
              <Legend />
              <Bar dataKey="budget" fill="#94a3b8" name="Budget" radius={[4, 4, 0, 0]} />
              <Bar dataKey="spent" fill="#ef4444" name="Spent" radius={[4, 4, 0, 0]} />
              <Bar dataKey="saved" fill="#22c55e" name="Saved" radius={[4, 4, 0, 0]} />
            </BarChart>
          ) : (
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month_label" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip formatter={(val) => `₹${val.toLocaleString()}`} />
              <Legend />
              <Line type="monotone" dataKey="budget" stroke="#94a3b8" strokeWidth={2} name="Budget" />
              <Line type="monotone" dataKey="spent" stroke="#ef4444" strokeWidth={2} name="Spent" />
              <Line type="monotone" dataKey="saved" stroke="#22c55e" strokeWidth={2} name="Saved" />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Table */}
      <div className="table-wrapper" style={{ marginTop: 18 }}>
        <table className="budget-table">
          <thead>
            <tr>
              <th>Month</th>
              <th>Budget</th>
              <th>Spent</th>
              <th>Saved</th>
              <th>Usage %</th>
              <th>Top Category</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {history.map((record) => (
              <tr key={record.id}>
                <td><FiCalendar style={{ marginRight: 4 }} />{record.month_label}</td>
                <td>₹{record.monthly_budget.toLocaleString()}</td>
                <td>₹{record.total_spent.toLocaleString()}</td>
                <td>₹{record.total_saved.toLocaleString()}</td>
                <td>{record.usage_percent}%</td>
                <td>{record.top_category || '—'}</td>
                <td>
                  <span className={`status-badge ${record.overspent ? 'danger' : 'safe'}`}>
                    {record.overspent ? 'Overspent' : 'On Track'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
