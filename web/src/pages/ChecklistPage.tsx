import { useEffect, useState } from 'react'
import { api, type ChecklistDay } from '../api'
import './pages.css'

export function ChecklistPage() {
  const [days, setDays] = useState<ChecklistDay[]>([])
  const [active, setActive] = useState('D1')
  const [draft, setDraft] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function reload() {
    const data = await api.checklist()
    setDays(data)
    const current = data.find((d) => d.day_key === active) ?? data[0]
    if (current) {
      setActive(current.day_key)
      setDraft(current.reflection)
    }
  }

  useEffect(() => {
    void reload().catch((err: Error) => setError(err.message))
  }, [])

  const day = days.find((d) => d.day_key === active)

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Checklist</p>
        <h1>7 日执行清单</h1>
        <p className="lede">每天打勾；睡前写 3 条发现。默读不算数。</p>
      </header>

      {error && <p className="error-text">{error}</p>}

      <div className="day-tabs">
        {days.map((d) => {
          const done = d.items.filter((i) => i.checked).length
          return (
            <button
              key={d.day_key}
              type="button"
              className={d.day_key === active ? 'primary' : ''}
              onClick={() => {
                setActive(d.day_key)
                setDraft(d.reflection)
              }}
            >
              {d.day_key} ({done}/{d.items.length})
            </button>
          )
        })}
      </div>

      {day && (
        <>
          <section className="card">
            <h2>
              {day.day_key} · {day.day_title}
            </h2>
            <ul className="check-list">
              {day.items.map((item) => (
                <li key={item.id}>
                  <label>
                    <input
                      type="checkbox"
                      checked={item.checked}
                      onChange={(e) => {
                        void api
                          .setChecklist(item.id, e.target.checked)
                          .then(() => reload())
                          .catch((err: Error) => setError(err.message))
                      }}
                    />
                    <span>{item.text}</span>
                  </label>
                </li>
              ))}
            </ul>
          </section>

          {day.day_key !== 'pre24h' && (
            <section className="card">
              <h2>今日复盘（3 条发现）</h2>
              <textarea
                rows={5}
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder={'1. …\n2. …\n3. …'}
              />
              <button
                type="button"
                className="primary"
                onClick={() => {
                  void api
                    .setReflection(day.day_key, draft)
                    .then(() => reload())
                    .catch((err: Error) => setError(err.message))
                }}
              >
                保存复盘
              </button>
            </section>
          )}
        </>
      )}
    </div>
  )
}
