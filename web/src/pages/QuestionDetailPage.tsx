import { useEffect, useState } from 'react'
import Markdown from 'react-markdown'
import { Link, useParams } from 'react-router-dom'
import { api, type QuestionDetail, type QuestionStatus } from '../api'
import './pages.css'

export function QuestionDetailPage() {
  const { id = '' } = useParams()
  const [q, setQ] = useState<QuestionDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [revealed, setRevealed] = useState(false)
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    setRevealed(false)
    void api
      .getQuestion(id)
      .then((data) => {
        setQ(data)
        setNotes(data.notes)
      })
      .catch((err: Error) => setError(err.message))
  }, [id])

  async function save(patch: { status?: QuestionStatus; score?: number; notes?: string }) {
    if (!id) return
    setSaving(true)
    try {
      const updated = await api.updateProgress(id, patch)
      setQ(updated)
      setNotes(updated.notes)
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败')
    } finally {
      setSaving(false)
    }
  }

  if (error) {
    return (
      <div className="page">
        <p className="error-text">{error}</p>
        <Link to="/questions">← 返回题库</Link>
      </div>
    )
  }

  if (!q) {
    return (
      <div className="page">
        <p className="muted">加载中…</p>
      </div>
    )
  }

  return (
    <div className="page">
      <Link className="back" to="/questions">
        ← 题库
      </Link>
      <header className="page-header">
        <p className="eyebrow">
          {q.id} · {q.module} · {q.priority}
        </p>
        <h1>{q.title}</h1>
        <p className="callout">案例中的数字为示范值，上场前请替换为真实经历。</p>
      </header>

      <section className="card practice">
        <h2>练习</h2>
        <p className="muted">先脱稿讲 1.5–2 分钟，再揭晓答案对照。</p>
        {!revealed ? (
          <button type="button" className="primary" onClick={() => setRevealed(true)}>
            揭晓答案
          </button>
        ) : (
          <div className="answer-stack">
            <article>
              <h3>答案</h3>
              <Markdown>{q.answer_md}</Markdown>
            </article>
            {q.followups_md && (
              <article>
                <h3>追问应对</h3>
                <Markdown>{q.followups_md}</Markdown>
              </article>
            )}
            {q.tradeoffs_md && (
              <article>
                <h3>取舍</h3>
                <Markdown>{q.tradeoffs_md}</Markdown>
              </article>
            )}
          </div>
        )}
      </section>

      <section className="card">
        <h2>进度</h2>
        <div className="actions">
          <button
            type="button"
            disabled={saving}
            onClick={() => void save({ status: 'reviewed' })}
          >
            标为已复习
          </button>
          <button
            type="button"
            className="primary"
            disabled={saving}
            onClick={() => void save({ status: 'recited' })}
          >
            标为已脱稿
          </button>
        </div>
        <label className="field">
          评分（1–5）
          <select
            value={q.score ?? ''}
            disabled={saving}
            onChange={(e) => {
              const value = e.target.value
              if (value) void save({ score: Number(value) })
            }}
          >
            <option value="">未评分</option>
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          笔记
          <textarea
            rows={4}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="薄弱点、要补的真实数字…"
          />
        </label>
        <button
          type="button"
          disabled={saving}
          onClick={() => void save({ notes })}
        >
          保存笔记
        </button>
        <p className="muted small">
          当前：{q.status}
          {q.score != null ? ` · ★ ${q.score}` : ''}
        </p>
      </section>
    </div>
  )
}
