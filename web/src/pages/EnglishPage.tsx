import { useEffect, useState } from 'react'
import Markdown from 'react-markdown'
import { api, type EnglishItem } from '../api'
import './pages.css'

export function EnglishPage() {
  const [items, setItems] = useState<EnglishItem[]>([])
  const [notes, setNotes] = useState<Record<string, string>>({})
  const [openId, setOpenId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function reload() {
    const data = await api.english()
    setItems(data)
    setNotes(Object.fromEntries(data.map((e) => [e.id, e.recording_note])))
  }

  useEffect(() => {
    void reload().catch((err: Error) => setError(err.message))
  }, [])

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">English</p>
        <h1>英文脚本练习</h1>
        <p className="lede">勾选已练；可用文字备注录音自查要点（无上传）。</p>
      </header>
      {error && <p className="error-text">{error}</p>}
      <ul className="stack-list">
        {items.map((e) => (
          <li key={e.id} className="card">
            <div className="card-head">
              <h2>{e.title}</h2>
              <span className={`pill ${e.practiced ? 'ok' : ''}`}>
                {e.practiced ? '已练' : '未练'}
              </span>
            </div>
            <div className="actions">
              <button
                type="button"
                className="primary"
                onClick={() =>
                  void api.patchEnglish(e.id, { practiced: !e.practiced }).then(reload)
                }
              >
                {e.practiced ? '取消已练' : '标为已练'}
              </button>
              <button type="button" onClick={() => setOpenId(openId === e.id ? null : e.id)}>
                {openId === e.id ? '收起' : '查看脚本'}
              </button>
            </div>
            {openId === e.id && (
              <>
                <div className="answer-stack">
                  <Markdown>{e.body_md}</Markdown>
                </div>
                <label className="field">
                  练习备注
                  <textarea
                    rows={3}
                    value={notes[e.id] ?? ''}
                    onChange={(ev) =>
                      setNotes((prev) => ({ ...prev, [e.id]: ev.target.value }))
                    }
                  />
                </label>
                <button
                  type="button"
                  onClick={() =>
                    void api
                      .patchEnglish(e.id, { recording_note: notes[e.id] ?? '' })
                      .then(reload)
                  }
                >
                  保存备注
                </button>
              </>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
