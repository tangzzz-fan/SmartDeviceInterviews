import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, type MockSession } from '../api'
import './pages.css'

export function MocksPage() {
  const [items, setItems] = useState<MockSession[]>([])
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  async function reload() {
    setItems(await api.listMocks())
  }

  useEffect(() => {
    void reload().catch((err: Error) => setError(err.message))
  }, [])

  async function create(roundKey: string) {
    try {
      const created = await api.createMock(roundKey)
      navigate(`/mocks/${created.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建失败')
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Mocks</p>
        <h1>模拟面试</h1>
        <p className="lede">
          通过标准：平均分 ≥ 4，且无单题 ≤ 2（对齐综合版 08）。
        </p>
      </header>
      {error && <p className="error-text">{error}</p>}

      <section className="card">
        <h2>新建场次</h2>
        <div className="actions">
          <button type="button" className="primary" onClick={() => void create('R1')}>
            第一轮 · 技术深挖
          </button>
          <button type="button" className="primary" onClick={() => void create('R2')}>
            第二轮 · 行为/英文
          </button>
          <button type="button" onClick={() => void create('phone')}>
            电话筛加练
          </button>
        </div>
      </section>

      <section className="card">
        <h2>历史记录</h2>
        {items.length === 0 ? (
          <p className="muted">还没有模拟记录。</p>
        ) : (
          <ul className="stack-list">
            {items.map((m) => (
              <li key={m.id}>
                <Link to={`/mocks/${m.id}`} className="question-row">
                  <span className="qid">#{m.id}</span>
                  <span className="qtitle">
                    {m.title} · {m.round_key}
                  </span>
                  <span className={`pill ${m.passed ? 'ok' : ''}`}>
                    {m.average != null ? `均分 ${m.average}` : '未评分'}
                    {m.passed ? ' · 通过' : ''}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

export function MockDetailPage() {
  const { id = '' } = useParams()
  const [mock, setMock] = useState<MockSession | null>(null)
  const [reflection, setReflection] = useState('')
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    void api
      .getMock(Number(id))
      .then((data) => {
        setMock(data)
        setReflection(data.reflection)
      })
      .catch((err: Error) => setError(err.message))
  }, [id])

  const scoredCount = useMemo(
    () => mock?.scores.filter((s) => s.score != null).length ?? 0,
    [mock],
  )

  async function saveScores(next: MockSession['scores']) {
    if (!mock) return
    const updated = await api.updateMock(mock.id, { scores: next })
    setMock(updated)
  }

  if (error) {
    return (
      <div className="page">
        <p className="error-text">{error}</p>
        <Link to="/mocks">← 返回</Link>
      </div>
    )
  }

  if (!mock) {
    return (
      <div className="page">
        <p className="muted">加载中…</p>
      </div>
    )
  }

  return (
    <div className="page">
      <Link className="back" to="/mocks">
        ← 模拟面试
      </Link>
      <header className="page-header">
        <p className="eyebrow">
          {mock.round_key} · #{mock.id}
        </p>
        <h1>{mock.title}</h1>
        <p className="lede">
          已评 {scoredCount}/{mock.scores.length} 项
          {mock.average != null && (
            <>
              {' '}
              · 均分 <strong>{mock.average}</strong>
              {' '}
              <span className={`pill ${mock.passed ? 'ok' : ''}`}>
                {mock.passed ? '通过' : '未通过'}
              </span>
            </>
          )}
        </p>
      </header>

      <section className="card">
        <h2>逐项打分（1–5）</h2>
        <ul className="skill-list">
          {mock.scores.map((item, index) => (
            <li key={item.id}>
              <strong>{item.label}</strong>
              <label className="field">
                分数
                <select
                  value={item.score ?? ''}
                  onChange={(e) => {
                    const value = e.target.value
                    const next = mock.scores.map((s, i) =>
                      i === index
                        ? { ...s, score: value ? Number(value) : null }
                        : s,
                    )
                    void saveScores(next).catch((err: Error) => setError(err.message))
                  }}
                >
                  <option value="">未评</option>
                  {[1, 2, 3, 4, 5].map((n) => (
                    <option key={n} value={n}>
                      {n}
                    </option>
                  ))}
                </select>
              </label>
            </li>
          ))}
        </ul>
      </section>

      <section className="card">
        <h2>复盘</h2>
        <textarea
          rows={5}
          value={reflection}
          onChange={(e) => setReflection(e.target.value)}
          placeholder="薄弱项、回炉题号、下次改进…"
        />
        <div className="actions">
          <button
            type="button"
            className="primary"
            onClick={() =>
              void api
                .updateMock(mock.id, { reflection })
                .then(setMock)
                .catch((err: Error) => setError(err.message))
            }
          >
            保存复盘
          </button>
          <button
            type="button"
            onClick={() =>
              void api
                .deleteMock(mock.id)
                .then(() => navigate('/mocks'))
                .catch((err: Error) => setError(err.message))
            }
          >
            删除场次
          </button>
        </div>
      </section>
    </div>
  )
}
