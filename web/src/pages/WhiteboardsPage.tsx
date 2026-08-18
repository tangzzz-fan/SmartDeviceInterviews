import { useEffect, useState } from 'react'
import Markdown from 'react-markdown'
import { api, type WhiteboardItem } from '../api'
import './pages.css'

export function WhiteboardsPage() {
  const [items, setItems] = useState<WhiteboardItem[]>([])
  const [openId, setOpenId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function reload() {
    setItems(await api.whiteboards())
  }

  useEffect(() => {
    void reload().catch((err: Error) => setError(err.message))
  }, [])

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Whiteboards</p>
        <h1>白板图解</h1>
        <p className="lede">白板 1–4 是 P0；画不出来等于不会。</p>
      </header>
      {error && <p className="error-text">{error}</p>}
      <ul className="stack-list">
        {items.map((w) => (
          <li key={w.id} className="card">
            <div className="card-head">
              <h2>
                {w.id} · {w.title}{' '}
                <span className="pill">{w.priority}</span>
              </h2>
              <span className="muted">练了 {w.practiced_count} 次 · {w.status}</span>
            </div>
            <div className="actions">
              <button
                type="button"
                className="primary"
                onClick={() =>
                  void api
                    .patchWhiteboard(w.id, { increment: true })
                    .then(reload)
                }
              >
                +1 练习
              </button>
              <button
                type="button"
                onClick={() =>
                  void api
                    .patchWhiteboard(w.id, { status: 'mastered' })
                    .then(reload)
                }
              >
                标为掌握
              </button>
              <button type="button" onClick={() => setOpenId(openId === w.id ? null : w.id)}>
                {openId === w.id ? '收起' : '查看内容'}
              </button>
            </div>
            {openId === w.id && (
              <div className="answer-stack">
                <Markdown>{w.body_md}</Markdown>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
