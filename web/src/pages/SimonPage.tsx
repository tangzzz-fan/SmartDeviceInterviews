import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type SimonGoal, type SimonNodeStatus } from '../api'
import './pages.css'

export function SimonPage() {
  const [goals, setGoals] = useState<SimonGoal[]>([])
  const [error, setError] = useState<string | null>(null)

  async function reload() {
    setGoals(await api.listSimon())
  }

  useEffect(() => {
    void reload().catch((err: Error) => setError(err.message))
  }, [])

  async function setScore(nodeId: string, score: number) {
    await api.patchSimonNode(nodeId, { self_score: score })
    await reload()
  }

  async function setStatus(nodeId: string, status: SimonNodeStatus) {
    await api.patchSimonNode(nodeId, { status })
    await reload()
  }

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Simon</p>
        <h1>西蒙练习 · 分解与反馈</h1>
        <p className="lede">
          把大目标拆成子技能；练完打 1–5 分。≥4 视为通过，≤2 标为卡住。
        </p>
      </header>
      {error && <p className="error-text">{error}</p>}

      {goals.map((g) => (
        <section key={g.id} className="card">
          <div className="card-head">
            <h2>{g.title}</h2>
            <span className="muted">
              {g.passed_count}/{g.total_count} 通过
            </span>
          </div>
          <p className="muted">{g.description}</p>
          <div className="bar" style={{ margin: '0.75rem 0' }}>
            <div
              className="bar-fill"
              style={{
                width: `${g.total_count ? Math.round((g.passed_count / g.total_count) * 100) : 0}%`,
              }}
            />
          </div>
          <ul className="skill-list">
            {g.nodes.map((n) => (
              <li key={n.id}>
                <strong>
                  {n.title}{' '}
                  <span className={`pill status-${n.status === 'passed' ? 'recited' : 'todo'}`}>
                    {n.status}
                  </span>
                </strong>
                <p className="muted small">{n.description}</p>
                <p className="small">
                  关联题：
                  {n.linked_question_ids.map((id) => (
                    <Link key={id} to={`/practice/feynman?q=${id}`} style={{ marginRight: 8 }}>
                      {id}
                    </Link>
                  ))}
                  {n.linked_whiteboard_ids.map((id) => (
                    <Link key={id} to="/whiteboards" style={{ marginRight: 8 }}>
                      {id}
                    </Link>
                  ))}
                </p>
                <div className="actions">
                  {[1, 2, 3, 4, 5].map((s) => (
                    <button
                      key={s}
                      type="button"
                      className={n.self_score === s ? 'primary' : ''}
                      onClick={() => void setScore(n.id, s)}
                    >
                      {s}
                    </button>
                  ))}
                  <button type="button" onClick={() => void setStatus(n.id, 'practicing')}>
                    练习中
                  </button>
                  <button type="button" onClick={() => void setStatus(n.id, 'passed')}>
                    通过
                  </button>
                  <button type="button" onClick={() => void setStatus(n.id, 'stuck')}>
                    卡住
                  </button>
                </div>
                <label className="field">
                  卡点备注
                  <textarea
                    rows={2}
                    defaultValue={n.blocker_note}
                    key={`${n.id}-${n.blocker_note}`}
                    onBlur={(e) =>
                      void api
                        .patchSimonNode(n.id, { blocker_note: e.target.value })
                        .then(reload)
                    }
                  />
                </label>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  )
}
