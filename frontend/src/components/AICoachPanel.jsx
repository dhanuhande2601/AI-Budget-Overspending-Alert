import { useEffect, useState } from 'react'
import {
  FiActivity,
  FiCalendar,
  FiCheckCircle,
  FiTarget,
  FiTrendingUp,
} from 'react-icons/fi'
import {
  getAICoach,
  getAIForecast,
  getSavingsRecommendation,
  getWeeklyChallenge,
} from '../api/budgetApi'

function AICoachPanel({ token, formatAmount }) {
  const [data, setData] = useState({
    coach: null,
    forecast: null,
    savings: null,
    challenge: null,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const money = formatAmount || ((amount) => `Rs. ${Number(amount || 0).toLocaleString('en-IN')}`)

  useEffect(() => {
    if (!token) return
    let isCurrent = true

    Promise.all([
      getAICoach(token).catch(() => null),
      getAIForecast(token).catch(() => null),
      getSavingsRecommendation(token).catch(() => null),
      getWeeklyChallenge(token).catch(() => null),
    ])
      .then(([coach, forecast, savings, challenge]) => {
        if (!isCurrent) return
        setData({ coach, forecast, savings, challenge })
      })
      .catch((err) => {
        if (isCurrent) setError(err.message)
      })
      .finally(() => {
        if (isCurrent) setLoading(false)
      })

    return () => { isCurrent = false }
  }, [token])

  if (loading) {
    return (
      <div className="panel ai-coach-panel">
        <p className="muted">Loading AI coach...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="panel ai-coach-panel">
        <p className="muted">AI coach is not available right now.</p>
      </div>
    )
  }

  const coach = data.coach?.coach || {}
  const forecast = data.forecast || {}
  const savings = data.savings || {}
  const challenge = data.challenge || {}

  return (
    <div className="panel ai-coach-panel">
      <div className="panel-heading compact">
        <div>
          <h2>AI Coach</h2>
          <p className="panel-subtitle">Daily guidance from your spending pattern.</p>
        </div>
      </div>

      <div className="ai-coach-metrics">
        <div>
          <FiTrendingUp aria-hidden="true" />
          <span>Forecast</span>
          <strong>{money(forecast.forecast)}</strong>
        </div>
        <div>
          <FiTarget aria-hidden="true" />
          <span>Save</span>
          <strong>{money(savings.recommended_savings)}</strong>
        </div>
      </div>

      {forecast.overspend > 0 && (
        <div className="danger-alert ai-coach-callout">
          Cut {money(forecast.reduce_per_day)}/day to avoid projected overspend.
        </div>
      )}

      <div className="ai-coach-list">
        {coach.habit && (
          <div>
            <FiActivity aria-hidden="true" />
            <p><strong>Habit:</strong> {coach.habit}</p>
          </div>
        )}
        {coach.today_challenge && (
          <div>
            <FiCheckCircle aria-hidden="true" />
            <p><strong>Today:</strong> {coach.today_challenge}</p>
          </div>
        )}
        {coach.smart_move && (
          <div>
            <FiTarget aria-hidden="true" />
            <p><strong>Smart move:</strong> {coach.smart_move}</p>
          </div>
        )}
      </div>

      {challenge.title && (
        <div className="ai-challenge-box">
          <div>
            <FiCalendar aria-hidden="true" />
            <strong>{challenge.title}</strong>
          </div>
          <p>{challenge.task}</p>
          <span>{challenge.reward}</span>
        </div>
      )}

      {savings.reason && (
        <p className="muted ai-coach-note">{savings.reason}</p>
      )}
    </div>
  )
}

export default AICoachPanel
