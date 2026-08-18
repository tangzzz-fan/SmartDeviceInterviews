import { useEffect, useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { api, type ColumnDocDetail, type ColumnDocListItem } from '../api'
import {
  getColumnMeta,
  groupColumnDocs,
  stemOf,
} from '../columns/catalog'
import { MarkdownView } from '../components/MarkdownView'
import './pages.css'

export function ColumnPage() {
  const { columnKey = 'smartglass', docId } = useParams()
  const [params, setParams] = useSearchParams()
  const track = params.get('track')
  const meta = getColumnMeta(columnKey)
  const [docs, setDocs] = useState<ColumnDocListItem[]>([])
  const [detail, setDetail] = useState<ColumnDocDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({})

  const groups = useMemo(
    () => groupColumnDocs(columnKey, docs, track),
    [columnKey, docs, track],
  )

  useEffect(() => {
    setError(null)
    void api
      .listColumn(columnKey)
      .then(setDocs)
      .catch((err: Error) => setError(err.message))
  }, [columnKey])

  useEffect(() => {
    if (!docs.length) return
    const grouped = groupColumnDocs(columnKey, docs, track)
    const next: Record<string, boolean> = {}
    for (const g of grouped) {
      next[g.section.id] = g.section.order <= 15
    }
    setOpenSections(next)
  }, [columnKey, track, docs])

  useEffect(() => {
    if (!docId || !docs.length) return
    const grouped = groupColumnDocs(columnKey, docs, track)
    for (const g of grouped) {
      if (g.items.some((i) => i.stem === docId || i.id === docId)) {
        setOpenSections((prev) => ({ ...prev, [g.section.id]: true }))
      }
    }
  }, [docId, columnKey, track, docs])

  useEffect(() => {
    if (!docId) {
      // default landing: README if present
      const readme = docs.find((d) => stemOf(d.id) === 'README')
      if (readme && !docId) {
        // show overview panel without forcing navigation
        setDetail(null)
      } else {
        setDetail(null)
      }
      return
    }
    setError(null)
    void api
      .getColumnDoc(columnKey, docId)
      .then(setDetail)
      .catch((err: Error) => setError(err.message))
  }, [columnKey, docId, docs])

  function setTrack(id: string | null) {
    const next = new URLSearchParams(params)
    if (id) next.set('track', id)
    else next.delete('track')
    setParams(next, { replace: true })
  }

  function toggleSection(id: string) {
    setOpenSections((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">
          <Link to="/columns">专栏</Link>
          {' / '}
          {meta?.short ?? columnKey}
        </p>
        <h1>{meta?.title ?? `专栏 · ${columnKey}`}</h1>
        <p className="lede">{meta?.lede ?? '独立栏目文档（Markdown + Mermaid）。'}</p>
        {meta?.pathHints && (
          <ol className="path-list inline-path">
            {meta.pathHints.map((h) => (
              <li key={h}>{h}</li>
            ))}
          </ol>
        )}
      </header>
      {error && <p className="error-text">{error}</p>}

      {meta?.tracks && (
        <div className="track-tabs">
          <button
            type="button"
            className={!track ? 'active' : ''}
            onClick={() => setTrack(null)}
          >
            全部
          </button>
          {meta.tracks.map((t) => (
            <button
              key={t.id}
              type="button"
              className={track === t.id ? 'active' : ''}
              onClick={() => setTrack(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
      )}

      <div className="column-layout wide-nav">
        <aside className="card column-nav">
          <h2>分区目录</h2>
          <p className="muted small">{docs.length} 篇 · 按学习路径分组</p>
          {docs.length === 0 ? (
            <p className="muted small">
              暂无文档。请运行：
              <code>python -m app.import_content</code>
            </p>
          ) : (
            groups.map((g) => {
              const open = openSections[g.section.id] !== false
              return (
                <div key={g.section.id} className="nav-section">
                  <button
                    type="button"
                    className="nav-section-head"
                    onClick={() => toggleSection(g.section.id)}
                    aria-expanded={open}
                  >
                    <span>
                      {open ? '▾' : '▸'} {g.section.label}
                    </span>
                    <span className="muted small">{g.items.length}</span>
                  </button>
                  {open && (
                    <ul className="stack-list compact-list">
                      {g.items.map((d) => (
                        <li key={d.id}>
                          <Link
                            to={`/column/${columnKey}/${encodeURIComponent(d.stem)}${
                              track ? `?track=${track}` : ''
                            }`}
                            className={
                              docId === d.stem || docId === d.id ? 'active-doc' : ''
                            }
                            title={d.title}
                          >
                            {d.label}
                          </Link>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )
            })
          )}
        </aside>

        <section className="card column-body">
          {!detail ? (
            <div className="column-landing">
              <h2>本专栏怎么读</h2>
              <p className="muted">
                左侧已按分区折叠。建议从导读开始，不要按字母顺序刷完全部文件。
              </p>
              {meta?.startDoc && (
                <p>
                  <Link
                    className="primary-link"
                    to={`/column/${columnKey}/${encodeURIComponent(meta.startDoc)}`}
                  >
                    打开 {meta.startDoc} →
                  </Link>
                </p>
              )}
              {meta?.tracks && (
                <div className="hub-mini">
                  {meta.tracks.map((t) => (
                    <button key={t.id} type="button" onClick={() => setTrack(t.id)}>
                      只看 {t.label}
                    </button>
                  ))}
                </div>
              )}
              <ul className="landing-toc">
                {groups.slice(0, 8).map((g) => (
                  <li key={g.section.id}>
                    <strong>{g.section.label}</strong>
                    <span className="muted"> · {g.items.length} 篇</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <>
              <h2>{detail.title}</h2>
              <p className="muted small">
                {stemOf(detail.id)} · {detail.filename}
              </p>
              <MarkdownView markdown={detail.body_md} />
            </>
          )}
        </section>
      </div>
    </div>
  )
}
