import { useEffect, useState } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

function App() {
  const [fixtures, setFixtures] = useState([])
  const [predictions, setPredictions] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/fixtures/today`)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load fixtures (${res.status})`)
        return res.json()
      })
      .then((data) => setFixtures(data.fixtures))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const loadPrediction = (fixture, index) => {
    const params = new URLSearchParams({
      home_team: fixture.home_team,
      away_team: fixture.away_team,
      league: fixture.league,
      date: fixture.date,
    })
    fetch(`${API_URL}/predictions?${params}`)
      .then((res) => {
        if (res.status === 404) throw new Error('Δεν υπάρχουν ιστορικά δεδομένα για πρόβλεψη')
        if (!res.ok) throw new Error(`Failed to load prediction (${res.status})`)
        return res.json()
      })
      .then((data) => setPredictions((prev) => ({ ...prev, [index]: data })))
      .catch((err) => setPredictions((prev) => ({ ...prev, [index]: { error: err.message } })))
  }

  return (
    <main className="container">
      <h1>Αγώνες Ημέρας</h1>
      <p className="subtitle">Live αποτελέσματα &amp; προβλέψεις 1X2</p>

      {loading && <p>Φόρτωση...</p>}
      {error && <p className="error">Σφάλμα: {error}</p>}

      {!loading && !error && fixtures.length === 0 && <p>Δεν υπάρχουν αγώνες σήμερα.</p>}

      <ul className="fixtures">
        {fixtures.map((fixture, index) => {
          const prediction = predictions[index]
          return (
            <li key={index} className="fixture">
              <div className="fixture-header">
                <span className="league">{fixture.league}</span>
                <span className="status">{fixture.status}</span>
              </div>
              <div className="teams">
                <span>{fixture.home_team}</span>
                <span className="score">
                  {fixture.home_score ?? '-'} : {fixture.away_score ?? '-'}
                </span>
                <span>{fixture.away_team}</span>
              </div>

              {!prediction && (
                <button onClick={() => loadPrediction(fixture, index)}>Πρόβλεψη</button>
              )}
              {prediction && prediction.error && (
                <p className="error">{prediction.error}</p>
              )}
              {prediction && !prediction.error && (
                <div className="prediction">
                  <p>
                    Αναμενόμενο σκορ: {prediction.expected_home_goals.toFixed(2)} -{' '}
                    {prediction.expected_away_goals.toFixed(2)}
                  </p>
                  <p>
                    1: {(prediction.home_win_prob * 100).toFixed(1)}% | X:{' '}
                    {(prediction.draw_prob * 100).toFixed(1)}% | 2:{' '}
                    {(prediction.away_win_prob * 100).toFixed(1)}%
                  </p>
                </div>
              )}
            </li>
          )
        })}
      </ul>
    </main>
  )
}

export default App
