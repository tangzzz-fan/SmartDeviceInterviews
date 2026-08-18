import { useEffect, useState } from 'react'
import { api, type StarItem } from '../api'
import { MarkdownView } from '../components/MarkdownView'
import './pages.css'

export function StoriesPage() {
  const [items, setItems] = useState<StarItem[]>([])
  const [openId, setOpenId] = useState<string | null>('S1')
  const [error, setError] = useState<string | null>(null)

  async function reload() {
    setItems(await api.stories())
  }

  useEffect(() => {
    void reload().catch((err: Error) => setError(err.message))
  }, [])

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">STAR</p>
        <h1>STAR 故事库</h1>
        <p className="lede">示范数字必须替换为真实经历；旗舰故事 S1 优先。</p>
      </header>
      {error && <p className="error-text">{error}</p>}
      <ul className="stack-list">
        {items.map((s) => (
          <li key={s.id} className="card">
            <div className="card-head">
              <h2>
                {s.id} · {s.title}
                {s.is_flagship && <span className="pill ok">旗舰</span>}
              </h2>
              <span className="muted">
                {s.filled_real_numbers ? '数字已填' : '待填数字'} ·{' '}
                {s.recited ? '已脱稿' : '未脱稿'}
              </span>
            </div>
            <div className="actions">
              <button
                type="button"
                onClick={() =>
                  void api
                    .patchStory(s.id, { filled_real_numbers: !s.filled_real_numbers })
                    .then(reload)
                }
              >
                {s.filled_real_numbers ? '取消数字已填' : '真实数字已填'}
              </button>
              <button
                type="button"
                className="primary"
                onClick={() =>
                  void api.patchStory(s.id, { recited: !s.recited }).then(reload)
                }
              >
                {s.recited ? '取消脱稿' : '标为已脱稿'}
              </button>
              <button type="button" onClick={() => setOpenId(openId === s.id ? null : s.id)}>
                {openId === s.id ? '收起' : '查看'}
              </button>
            </div>
            {openId === s.id && (
              <div className="answer-stack">
                <MarkdownView markdown={s.body_md} />
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
