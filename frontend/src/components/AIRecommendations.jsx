function AIRecommendations({ alerts = [] }) {
  if (!alerts.length) {
    return (
      <div className="card">
        <h2>🤖 AI Recommendations</h2>
        <p>No recommendations available.</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h2>🤖 AI Recommendations</h2>

      {alerts.map((alert, index) => (
        <div
          key={index}
          className="alert-card"
          style={{
            border: "1px solid #ddd",
            borderRadius: "10px",
            padding: "12px",
            marginBottom: "12px",
            background: "#f9fafb"
          }}
        >
          <h4>{alert.category}</h4>

          <p>
            <strong>Alert:</strong> {alert.message}
          </p>

          {alert.ai_recommendation && (
            <div
              style={{
                background: "#eef6ff",
                padding: "10px",
                borderRadius: "8px",
                marginTop: "10px"
              }}
            >
              <strong>🤖 AI Advice:</strong>
              <p>{alert.ai_recommendation}</p>
            </div>
          )}

          {alert.festival_prediction && (
            <div
              style={{
                background: "#FEF9C3",
                color: "#854D0E",
                padding: "10px",
                borderRadius: "8px",
                marginTop: "10px"
              }}
            >
              🎉 {alert.festival_prediction}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export default AIRecommendations