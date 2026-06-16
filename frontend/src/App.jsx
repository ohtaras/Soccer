import { useEffect, useState } from 'react'
import './App.css'
import { getCountryFlag } from './countryFlags'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const STATUS_LABELS = {
  pre: 'Προγρ.',
  in: 'LIVE',
  post: 'Τελ.',
}

const TZ = 'Europe/Athens'

function formatTime(isoDate) {
  if (!isoDate) return '--:--'
  const date = new Date(isoDate)
  return date.toLocaleTimeString('el-GR', { hour: '2-digit', minute: '2-digit', timeZone: TZ })
}

function teamLogoUrl(teamId) {
  return teamId ? `https://images.fotmob.com/image_resources/logo/teamlogo/${teamId}_small.png` : null
}

function TeamLogo({ teamId, name }) {
  const [hidden, setHidden] = useState(false)
  const url = teamLogoUrl(teamId)
  if (!url || hidden) return <span className="team-logo team-logo-placeholder" />
  return <img className="team-logo" src={url} alt="" onError={() => setHidden(true)} />
}

function groupByLeague(fixtures) {
  const groups = []
  const indexByLeague = new Map()

  fixtures.forEach((fixture, index) => {
    let group = indexByLeague.get(fixture.league)
    if (!group) {
      group = { league: fixture.league, matches: [] }
      indexByLeague.set(fixture.league, group)
      groups.push(group)
    }
    group.matches.push({ fixture, index })
  })

  return groups
}

function toDateInputValue(d) {
  return d.toLocaleDateString('sv', { timeZone: TZ })
}

function addDays(d, days) {
  const result = new Date(d)
  result.setDate(result.getDate() + days)
  return result
}

function App() {
  const [selectedDate, setSelectedDate] = useState(() => new Date())
  const [fixtures, setFixtures] = useState([])
  const [predictableLeagues, setPredictableLeagues] = useState(new Set())
  const [predictions, setPredictions] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/predictions/leagues`)
      .then((res) => (res.ok ? res.json() : []))
      .then((leagues) => setPredictableLeagues(new Set(leagues)))
      .catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    setError(null)
    setPredictions({})
    fetch(`${API_URL}/fixtures/today?date=${toDateInputValue(selectedDate)}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load fixtures (${res.status})`)
        return res.json()
      })
      .then((data) => setFixtures(data.fixtures))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [selectedDate])

  const loadPrediction = (fixture, index) => {
    const params = new URLSearchParams({
      home_team: fixture.home_team,
      away_team: fixture.away_team,
      league: fixture.league,
      date: fixture.date,
    })
    fetch(`${API_URL}/predictions?${params}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load prediction (${res.status})`)
        return res.json()
      })
      .then((data) => setPredictions((prev) => ({ ...prev, [index]: data })))
      .catch(() => setPredictions((prev) => ({ ...prev, [index]: { error: true } })))
  }

  useEffect(() => {
    if (predictableLeagues.size === 0) return
    fixtures.forEach((fixture, index) => {
      if (predictableLeagues.has(fixture.league)) {
        loadPrediction(fixture, index)
      }
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fixtures, predictableLeagues])

  const groups = groupByLeague(fixtures)

  const isToday = toDateInputValue(selectedDate) === toDateInputValue(new Date())
  const dateLabel = selectedDate.toLocaleDateString('el-GR', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    timeZone: TZ,
  })

  return (
    <main className="container">
      <div className="app-logo">
        <svg viewBox="0 0 100 100" className="logo-ball" xmlns="http://www.w3.org/2000/svg">
          <circle cx="50" cy="50" r="46" fill="#f0f0f0" stroke="#1e293b" strokeWidth="3"/>
          <polygon points="50,30 63,40 58,55 42,55 37,40" fill="#1e293b"/>
          <polygon points="62,14 76,18 82,32 68,40 63,28" fill="#1e293b"/>
          <polygon points="26,58 42,55 37,40 18,32 14,48" fill="#1e293b"/>
          <polygon points="74,58 58,55 68,40 82,32 86,48" fill="#f0f0f0" stroke="#1e293b" strokeWidth="1.5"/>
          <polygon points="50,4 62,14 63,28 50,30 37,28 38,14" fill="#f0f0f0" stroke="#1e293b" strokeWidth="1.5"/>
          <polygon points="18,32 24,18 38,14 37,28 32,28" fill="#f0f0f0" stroke="#1e293b" strokeWidth="1.5"/>
          <polygon points="26,58 30,72 44,78 56,78 70,72 74,58 58,55 42,55" fill="#1e293b"/>
        </svg>
        <h1>Μαλακίες του Σπύρου</h1>
      </div>
      <p className="subtitle">Live αποτελέσματα &amp; προβλέψεις</p>

      <div className="date-nav">
        <button onClick={() => setSelectedDate((d) => addDays(d, -1))}>‹ Χθες</button>
        <span className="date-label">{isToday ? `Σήμερα, ${dateLabel}` : dateLabel}</span>
        <button onClick={() => setSelectedDate((d) => addDays(d, 1))}>Αύριο ›</button>
      </div>

      {loading && <p>Φόρτωση...</p>}
      {error && <p className="error">Σφάλμα: {error}</p>}

      {!loading && !error && fixtures.length === 0 && <p>Δεν υπάρχουν αγώνες αυτή την ημέρα.</p>}

      {groups.map((group) => (
        <section className="league-group" key={group.league}>
          <h2 className="league-title">
            <span className="flag">{getCountryFlag(group.league)}</span> {group.league}
          </h2>
          <ul className="fixtures">
            {group.matches.map(({ fixture, index }) => {
              const prediction = predictions[index]
              return (
                <li key={index} className="fixture">
                  <div className="fixture-row">
                    <span className={`status status-${fixture.status}`}>
                      {fixture.status === 'pre'
                        ? formatTime(fixture.date)
                        : fixture.status === 'in'
                          ? fixture.minute || STATUS_LABELS.in
                          : STATUS_LABELS.post}
                    </span>
                    <span className="team home-team">
                      <span className="team-name">{fixture.home_team}</span>
                      <TeamLogo teamId={fixture.home_team_id} />
                    </span>
                    <span className="score">
                      {fixture.home_score ?? '-'} : {fixture.away_score ?? '-'}
                    </span>
                    <span className="team away-team">
                      <TeamLogo teamId={fixture.away_team_id} />
                      <span className="team-name">{fixture.away_team}</span>
                    </span>
                  </div>

                  {prediction && !prediction.error && (
                    <div className="prediction">
                      <p className="pred-goals">
                        Αναμ. σκορ: {prediction.expected_home_goals.toFixed(2)} – {prediction.expected_away_goals.toFixed(2)}
                      </p>
                      <p className="pred-1x2">
                        1: {(prediction.home_win_prob * 100).toFixed(1)}% &nbsp;|&nbsp;
                        X: {(prediction.draw_prob * 100).toFixed(1)}% &nbsp;|&nbsp;
                        2: {(prediction.away_win_prob * 100).toFixed(1)}%
                      </p>
                      <p className="pred-markets">
                        GG: {(prediction.both_teams_score_prob * 100).toFixed(1)}% &nbsp;|&nbsp;
                        Over 2.5: {(prediction.over_25_prob * 100).toFixed(1)}% &nbsp;|&nbsp;
                        Over 1.5: {(prediction.over_15_prob * 100).toFixed(1)}%
                      </p>
                      {prediction.best_bet && (
                        <p className="pred-best">
                          ★ {prediction.best_bet.market} &nbsp;
                          <span className="pred-best-prob">
                            {(prediction.best_bet.probability * 100).toFixed(1)}%
                          </span>
                        </p>
                      )}
                    </div>
                  )}
                </li>
              )
            })}
          </ul>
        </section>
      ))}
    </main>
  )
}

export default App
