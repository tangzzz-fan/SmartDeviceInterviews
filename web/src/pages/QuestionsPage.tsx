import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api, type QuestionListItem, type QuestionStatus } from '../api'
import './pages.css'

const STATUS_LABEL: Record<QuestionStatus, string> = {
  todo: '未开始',
  reviewed: '已复习',
  recited: '已脱稿',
}

export function QuestionsPage() {
  const [params, setParams] = useSearchParams()
  const module = params.get('module') ?? ''
  const priority = params.get('priority') ?? ''
  const status = (params.get('status') ?? '') as QuestionStatus | ''

  const [items, setItems] = useState<QuestionListItem[]>([])
  const [allModules, setAllModules] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Load all once for module dropdown options
    void api.listQuestions().then((all) => {
      const modules = [...new Set(all.map((q) => q.module))].sort()
      setAllModules(modules)
    })
  }, [])

  useEffect(() => {
    setLoading(true)
    void api
      .listQuestions({
        module: module || undefined,
        priority: priority || undefined,
        status: status || undefined,
      })
      .then(setItems)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [module, priority, status])

  const priorities = useMemo(
    () => [...new Set(items.map((q) => q.priority))].sort(),
    [items],
  )

  function updateFilter(key: string, value: string) {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next)
  }

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Question bank</p>
        <h1>题库</h1>
        <p className="lede">先尝试脱稿，再揭晓答案。默读不算会。</p>
      </header>

      <div className="filters row">
        <label>
          模块
          <select value={module} onChange={(e) => updateFilter('module', e.target.value)}>
            <option value="">全部</option>
            {allModules.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </label>
        <label>
          优先级
          <select
            value={priority}
            onChange={(e) => updateFilter('priority', e.target.value)}
          >
            <option value="">全部</option>
            <option value="P0">P0</option>
            <option value="P1">P1</option>
            {priorities
              .filter((p) => p !== 'P0' && p !== 'P1')
              .map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
          </select>
        </label>
        <label>
          状态
          <select
            value={status}
            onChange={(e) => updateFilter('status', e.target.value)}
          >
            <option value="">全部</option>
            <option value="todo">未开始</option>
            <option value="reviewed">已复习</option>
            <option value="recited">已脱稿</option>
          </select>
        </label>
      </div>

      {loading && <p className="muted">加载中…</p>}
      {error && <p className="error-text">{error}</p>}
      {!loading && !error && (
        <p className="muted small">共 {items.length} 题</p>
      )}

      <ul className="question-list">
        {items.map((q) => (
          <li key={q.id}>
            <Link to={`/questions/${q.id}`} className="question-row">
              <span className="qid">{q.id}</span>
              <span className="qtitle">{q.title}</span>
              <span className={`pill status-${q.status}`}>{STATUS_LABEL[q.status]}</span>
              {q.score != null && <span className="score">★ {q.score}</span>}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
