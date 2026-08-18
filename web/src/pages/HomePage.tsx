import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type DashboardResponse, type HealthResponse } from '../api'
import './pages.css'

export function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [healthError, setHealthError] = useState<string | null>(null)
  const [dash, setDash] = useState<DashboardResponse | null>(null)

  useEffect(() => {
    void api
      .health()
      .then(setHealth)
      .catch((err: Error) => setHealthError(err.message))
    void api
      .dashboard()
      .then(setDash)
      .catch(() => setDash(null))
  }, [])

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Dashboard</p>
        <h1>学习概览</h1>
        <p className="lede">
          全题库进度一览。改 Markdown 后运行{' '}
          <code>python -m app.import_content</code> 同步。
        </p>
      </header>

      <section className="card">
        <h2>API</h2>
        {healthError && <p className="error-text">后端不可用：{healthError}</p>}
        {health && (
          <p>
            <span className="pill ok">{health.status}</span> {health.service}
          </p>
        )}
      </section>

      <section className="card">
        <div className="card-head">
          <h2>练习法</h2>
          <span>
            <Link to="/practice/feynman">费曼</Link>
            {' · '}
            <Link to="/practice/simon">西蒙</Link>
          </span>
        </div>
        {dash?.open_simon_nodes && dash.open_simon_nodes.length > 0 ? (
          <ul className="weak-list">
            {dash.open_simon_nodes.map((n) => (
              <li key={n.id}>
                <Link to="/practice/simon">
                  <span className="qid">{n.status}</span>
                  <span>
                    {n.goal_title} · {n.title}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">用费曼盲答打结构，用西蒙树打薄弱子技能。</p>
        )}
      </section>

      <section className="card">
        <div className="card-head">
          <h2>专栏（分栏材料）</h2>
          <Link to="/columns">总览 →</Link>
        </div>
        <p className="muted">
          Glass 眼镜叙事 · Algo 算法工程化 · MIT 四线攻坚。与综合版题库分栏，按分区阅读。
        </p>
        <p>
          <Link to="/column/smartglass">Glass</Link>
          {' · '}
          <Link to="/column/algolab">Algo</Link>
          {' · '}
          <Link to="/column/mit">MIT</Link>
        </p>
      </section>

      <section className="card">
        <div className="card-head">
          <h2>模拟面试</h2>
          <Link to="/mocks">进入模拟面 →</Link>
        </div>
        {!dash?.latest_mock ? (
          <p className="muted">还没有模拟记录。按 08 脚本跑一轮并打分。</p>
        ) : (
          <p>
            最近：
            <Link to={`/mocks/${dash.latest_mock.id}`}>
              {dash.latest_mock.title}
            </Link>
            {dash.latest_mock.average != null && (
              <>
                {' '}
                · 均分 <strong>{dash.latest_mock.average}</strong>
              </>
            )}{' '}
            <span className={`pill ${dash.latest_mock.passed ? 'ok' : ''}`}>
              {dash.latest_mock.passed ? '通过' : '未通过 / 未评完'}
            </span>
          </p>
        )}
      </section>

      <section className="card">
        <div className="card-head">
          <h2>题库总览</h2>
          <Link to="/questions">进入题库 →</Link>
        </div>
        {!dash || dash.total === 0 ? (
          <p className="muted">
            暂无题目。请运行：
            <code>cd backend && python -m app.import_content</code>
          </p>
        ) : (
          <>
            <ul className="stats">
              <li>
                <strong>{dash.total}</strong>
                <span>题目</span>
              </li>
              <li>
                <strong>{dash.reviewed}</strong>
                <span>已复习</span>
              </li>
              <li>
                <strong>{dash.recited}</strong>
                <span>已脱稿</span>
              </li>
            </ul>

            <h3 className="subhead">按模块</h3>
            <ul className="module-list">
              {dash.modules.map((m) => {
                const done = m.recited
                const pct = m.total ? Math.round((done / m.total) * 100) : 0
                return (
                  <li key={m.module}>
                    <Link to={`/questions?module=${encodeURIComponent(m.module)}`}>
                      <div className="module-row">
                        <strong>{m.module}</strong>
                        <span>
                          {done}/{m.total} 脱稿 · {pct}%
                        </span>
                      </div>
                      <div className="bar">
                        <div className="bar-fill" style={{ width: `${pct}%` }} />
                      </div>
                    </Link>
                  </li>
                )
              })}
            </ul>

            {dash.weak_questions.length > 0 && (
              <>
                <h3 className="subhead">待加强</h3>
                <ul className="weak-list">
                  {dash.weak_questions.map((w) => (
                    <li key={w.id}>
                      <Link to={`/questions/${w.id}`}>
                        <span className="qid">{w.id}</span>
                        <span>{w.title}</span>
                        {w.score != null && <span className="score">★ {w.score}</span>}
                      </Link>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </>
        )}
      </section>
    </div>
  )
}
