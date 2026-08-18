import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, type ColumnDocDetail, type ColumnDocListItem } from '../api'
import { MarkdownView } from '../components/MarkdownView'
import './pages.css'

const COLUMN = 'smartglass'

export function ColumnPage() {
  const { docId } = useParams()
  const [docs, setDocs] = useState<ColumnDocListItem[]>([])
  const [detail, setDetail] = useState<ColumnDocDetail | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    void api
      .listColumn(COLUMN)
      .then(setDocs)
      .catch((err: Error) => setError(err.message))
  }, [])

  useEffect(() => {
    if (!docId) {
      setDetail(null)
      return
    }
    void api
      .getColumnDoc(COLUMN, docId)
      .then(setDetail)
      .catch((err: Error) => setError(err.message))
  }, [docId])

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Column</p>
        <h1>专栏 · SmartGlass</h1>
        <p className="lede">
          商汤眼镜故事材料（复制自 SmartGlassInterview）。与 Nirva 题库分栏；音频口径见专栏 README。
        </p>
      </header>
      {error && <p className="error-text">{error}</p>}

      <div className="column-layout">
        <aside className="card column-nav">
          <h2>目录</h2>
          {docs.length === 0 ? (
            <p className="muted small">
              暂无文档。请运行：
              <code>python -m app.import_content --path ../专栏_SmartGlass</code>
            </p>
          ) : (
            <ul className="stack-list">
              {docs.map((d) => {
                const stem = d.id.includes(':') ? d.id.split(':').slice(1).join(':') : d.id
                return (
                  <li key={d.id}>
                    <Link
                      to={`/column/smartglass/${encodeURIComponent(stem)}`}
                      className={docId === stem || docId === d.id ? 'active-doc' : ''}
                    >
                      {d.title}
                    </Link>
                  </li>
                )
              })}
            </ul>
          )}
        </aside>

        <section className="card column-body">
          {!detail ? (
            <p className="muted">从左侧选择一篇文档。支持 Mermaid 图。</p>
          ) : (
            <>
              <h2>{detail.title}</h2>
              <p className="muted small">{detail.filename}</p>
              <MarkdownView markdown={detail.body_md} />
            </>
          )}
        </section>
      </div>
    </div>
  )
}
