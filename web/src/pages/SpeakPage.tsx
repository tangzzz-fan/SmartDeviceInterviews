import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api, type SpeakItem } from '../api'
import './pages.css'

export function SpeakPage() {
  const [params, setParams] = useSearchParams()
  const focus = params.get('id') ?? ''
  const [items, setItems] = useState<SpeakItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [localText, setLocalText] = useState<Record<string, string>>({})

  const selected = useMemo(
    () => items.find((i) => i.id === focus) ?? items[0] ?? null,
    [items, focus],
  )

  useEffect(() => {
    void api
      .listSpeak()
      .then((list) => {
        setItems(list)
        const texts: Record<string, string> = {}
        for (const i of list) texts[i.id] = i.draft_text
        setLocalText(texts)
        if (!focus && list[0]) {
          setParams({ id: list[0].id }, { replace: true })
        }
      })
      .catch((err: Error) => setError(err.message))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const done = items.filter((i) => i.status === 'revealed' || i.filled).length

  async function save(id: string) {
    setSaving(true)
    setError(null)
    try {
      const updated = await api.saveSpeak(id, localText[id] ?? '')
      setItems((prev) => prev.map((i) => (i.id === id ? updated : i)))
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSaving(false)
    }
  }

  async function reveal(id: string) {
    setSaving(true)
    setError(null)
    try {
      await api.saveSpeak(id, localText[id] ?? '')
      const updated = await api.revealSpeak(id)
      setItems((prev) => prev.map((i) => (i.id === id ? updated : i)))
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSaving(false)
    }
  }

  async function reset(id: string) {
    setSaving(true)
    try {
      const updated = await api.resetSpeak(id)
      setItems((prev) => prev.map((i) => (i.id === id ? updated : i)))
      setLocalText((prev) => ({ ...prev, [id]: '' }))
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Practice · T15</p>
        <h1>关闭口述</h1>
        <p className="lede">
          Glass 模式：先盲写，再揭晓对照。每条已映射到 Nirva 题库/白板（不是 Glass
          JD 题号）。进度 {done}/{items.length}
        </p>
      </header>
      {error && <p className="error-text">{error}</p>}

      <div className="column-layout">
        <aside className="card column-nav">
          <h2>口述目录</h2>
          <ul className="stack-list">
            {items.map((i) => (
              <li key={i.id}>
                <button
                  type="button"
                  className={`linkish ${selected?.id === i.id ? 'active-doc' : ''}`}
                  onClick={() => setParams({ id: i.id })}
                >
                  {i.status === 'revealed' ? '✓ ' : i.filled ? '· ' : ''}
                  {i.title}
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <section className="card column-body">
          {!selected ? (
            <p className="muted">加载中…</p>
          ) : (
            <>
              <h2>{selected.title}</h2>
              <p className="muted small">
                建议时长 {selected.seconds}
                {selected.glass_source_id
                  ? ` · 映射自 Glass ${selected.glass_source_id}`
                  : ''}
              </p>
              <p>
                <strong>提问：</strong>
                {selected.ask}
              </p>
              <p className="muted small">
                关联题：
                {selected.linked_question_ids.map((qid) => (
                  <Link key={qid} to={`/questions/${qid}`} style={{ marginRight: 8 }}>
                    {qid}
                  </Link>
                ))}
                {selected.linked_whiteboard_ids.length > 0 && (
                  <>
                    · 白板：
                    {selected.linked_whiteboard_ids.map((wid) => (
                      <Link
                        key={wid}
                        to={`/whiteboards#${wid}`}
                        style={{ marginRight: 8 }}
                      >
                        {wid}
                      </Link>
                    ))}
                  </>
                )}
              </p>

              <label className="field">
                <span>盲写区（提交前不显示参考）</span>
                <textarea
                  rows={10}
                  value={localText[selected.id] ?? ''}
                  onChange={(e) =>
                    setLocalText((prev) => ({
                      ...prev,
                      [selected.id]: e.target.value,
                    }))
                  }
                  placeholder="不看稿，先写出口述骨架…"
                />
              </label>

              <div className="row-actions">
                <button type="button" disabled={saving} onClick={() => void save(selected.id)}>
                  保存草稿
                </button>
                <button
                  type="button"
                  className="primary"
                  disabled={saving}
                  onClick={() => void reveal(selected.id)}
                >
                  揭晓对照
                </button>
                <button type="button" disabled={saving} onClick={() => void reset(selected.id)}>
                  重置
                </button>
                <Link to={`/practice/feynman?q=${selected.linked_question_ids[0] ?? ''}`}>
                  用关联题做费曼 →
                </Link>
              </div>

              {selected.status === 'revealed' && selected.reference && (
                <blockquote className="speak-ref">
                  <strong>对照参考（Nirva 口径）</strong>
                  <p style={{ whiteSpace: 'pre-wrap' }}>{selected.reference}</p>
                </blockquote>
              )}
            </>
          )}
        </section>
      </div>
    </div>
  )
}
