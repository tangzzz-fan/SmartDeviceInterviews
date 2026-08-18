import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  api,
  type FeynmanChecklist,
  type FeynmanDraft,
  type QuestionListItem,
} from '../api'
import { MarkdownView } from '../components/MarkdownView'
import './pages.css'

const emptyChecklist = (): FeynmanChecklist => ({
  conclusion: false,
  mechanism: false,
  example: false,
  tradeoff: false,
  metric: false,
  followup: false,
})

export function FeynmanPage() {
  const [params, setParams] = useSearchParams()
  const qid = params.get('q') ?? ''
  const [questions, setQuestions] = useState<QuestionListItem[]>([])
  const [draft, setDraft] = useState<FeynmanDraft | null>(null)
  const [form, setForm] = useState({
    conclusion: '',
    mechanism: '',
    example: '',
    tradeoff: '',
    metric: '',
  })
  const [checklist, setChecklist] = useState<FeynmanChecklist>(emptyChecklist())
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [seconds, setSeconds] = useState(0)
  const [timerOn, setTimerOn] = useState(false)

  const selected = useMemo(
    () => questions.find((q) => q.id === qid) ?? null,
    [questions, qid],
  )

  const revealed =
    draft?.status === 'submitted' || draft?.status === 'compared'

  useEffect(() => {
    void api.listQuestions().then(setQuestions).catch((err: Error) => setError(err.message))
  }, [])

  useEffect(() => {
    if (!qid) {
      setDraft(null)
      return
    }
    void api
      .getFeynmanByQuestion(qid)
      .then((d) => {
        if (d) {
          setDraft(d)
          setForm({
            conclusion: d.conclusion,
            mechanism: d.mechanism,
            example: d.example,
            tradeoff: d.tradeoff,
            metric: d.metric,
          })
          setChecklist(d.checklist)
        } else {
          setDraft(null)
          setForm({
            conclusion: '',
            mechanism: '',
            example: '',
            tradeoff: '',
            metric: '',
          })
          setChecklist(emptyChecklist())
        }
      })
      .catch((err: Error) => setError(err.message))
  }, [qid])

  useEffect(() => {
    if (!timerOn) return
    const id = window.setInterval(() => setSeconds((s) => s + 1), 1000)
    return () => window.clearInterval(id)
  }, [timerOn])

  async function saveDraft() {
    if (!qid) return
    setSaving(true)
    try {
      const d = await api.saveFeynman({
        question_id: qid,
        ...form,
        checklist,
      })
      setDraft(d)
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败')
    } finally {
      setSaving(false)
    }
  }

  async function submit(markRecited: boolean) {
    if (!qid) return
    setSaving(true)
    try {
      const current = await api.saveFeynman({
        question_id: qid,
        ...form,
        checklist,
      })
      const d = await api.submitFeynman(current.id, {
        mark_recited: markRecited,
        checklist,
      })
      setDraft(d)
      setTimerOn(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : '提交失败')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Feynman</p>
        <h1>费曼练习 · 盲答再对照</h1>
        <p className="lede">
          先按五层写出自己的答案（至少 3 项），提交后才揭晓原文。默读不算会。
        </p>
      </header>

      {error && <p className="error-text">{error}</p>}

      <section className="card">
        <label className="field">
          选题
          <select
            value={qid}
            onChange={(e) => {
              const next = new URLSearchParams(params)
              if (e.target.value) next.set('q', e.target.value)
              else next.delete('q')
              setParams(next)
              setSeconds(0)
              setTimerOn(false)
            }}
          >
            <option value="">选择题目…</option>
            {questions.map((q) => (
              <option key={q.id} value={q.id}>
                {q.id} · {q.title}
              </option>
            ))}
          </select>
        </label>
        {selected && (
          <p className="muted">
            {selected.id} · {selected.module} · {selected.priority}
            {' · '}
            <Link to={`/questions/${selected.id}`}>打开题库页</Link>
          </p>
        )}
        <div className="actions">
          <button type="button" onClick={() => setTimerOn((v) => !v)}>
            {timerOn ? '暂停计时' : '开始计时'}
          </button>
          <span className="muted">
            {Math.floor(seconds / 60)}:{String(seconds % 60).padStart(2, '0')}
            （建议 90s–2min）
          </span>
        </div>
      </section>

      {qid && (
        <>
          <section className="card">
            <h2>你的五层输出（盲答）</h2>
            {(
              [
                ['conclusion', '1. 结论（一句话）'],
                ['mechanism', '2. 机制（怎么工作）'],
                ['example', '3. 案例 / 缺口话术'],
                ['tradeoff', '4. 取舍'],
                ['metric', '5. 指标或为何暂无'],
              ] as const
            ).map(([key, label]) => (
              <label key={key} className="field">
                {label}
                <textarea
                  rows={key === 'conclusion' ? 2 : 3}
                  disabled={revealed}
                  value={form[key]}
                  onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                />
              </label>
            ))}
            <div className="actions">
              <button type="button" disabled={saving || revealed} onClick={() => void saveDraft()}>
                保存草稿
              </button>
              <button
                type="button"
                className="primary"
                disabled={saving || revealed}
                onClick={() => void submit(false)}
              >
                提交并对照原文
              </button>
              <button
                type="button"
                disabled={saving || revealed}
                onClick={() => void submit(true)}
              >
                对照并标为已脱稿
              </button>
              {draft && revealed && (
                <button
                  type="button"
                  onClick={() =>
                    void api.resetFeynman(draft.id).then((d) => {
                      setDraft(d)
                      setForm({
                        conclusion: '',
                        mechanism: '',
                        example: '',
                        tradeoff: '',
                        metric: '',
                      })
                      setChecklist(emptyChecklist())
                      setSeconds(0)
                    })
                  }
                >
                  再练一版（新草稿）
                </button>
              )}
            </div>
          </section>

          {revealed && draft && (
            <>
              <section className="card">
                <h2>五层检查表</h2>
                {(
                  [
                    ['conclusion', '第一句是结论'],
                    ['mechanism', '有机制'],
                    ['example', '有案例或缺口话术'],
                    ['tradeoff', '有取舍'],
                    ['metric', '有指标或说明'],
                    ['followup', '能承受一个追问'],
                  ] as const
                ).map(([key, label]) => (
                  <label key={key} className="check-inline">
                    <input
                      type="checkbox"
                      checked={checklist[key]}
                      onChange={(e) =>
                        setChecklist((c) => ({ ...c, [key]: e.target.checked }))
                      }
                    />
                    {label}
                  </label>
                ))}
                <button
                  type="button"
                  className="primary"
                  onClick={() =>
                    void api
                      .submitFeynman(draft.id, { checklist })
                      .then(setDraft)
                  }
                >
                  保存检查表
                </button>
              </section>

              <section className="card">
                <h2>对照原文</h2>
                <div className="compare-grid">
                  <div>
                    <h3>你的答案</h3>
                    <pre className="draft-preview">
                      {[
                        form.conclusion && `结论：${form.conclusion}`,
                        form.mechanism && `机制：${form.mechanism}`,
                        form.example && `案例：${form.example}`,
                        form.tradeoff && `取舍：${form.tradeoff}`,
                        form.metric && `指标：${form.metric}`,
                      ]
                        .filter(Boolean)
                        .join('\n\n')}
                    </pre>
                  </div>
                  <div>
                    <h3>标准答案</h3>
                    <MarkdownView markdown={draft.reference_answer_md ?? ''} />
                    {draft.reference_followups_md && (
                      <>
                        <h3>追问</h3>
                        <MarkdownView markdown={draft.reference_followups_md} />
                      </>
                    )}
                    {draft.reference_tradeoffs_md && (
                      <>
                        <h3>取舍</h3>
                        <MarkdownView markdown={draft.reference_tradeoffs_md} />
                      </>
                    )}
                  </div>
                </div>
              </section>
            </>
          )}
        </>
      )}
    </div>
  )
}
