import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, type ColumnDocDetail, type ColumnDocListItem } from '../api'
import { MarkdownView } from '../components/MarkdownView'
import './pages.css'

const META: Record<string, { title: string; lede: string }> = {
  smartglass: {
    title: '专栏 · SmartGlass',
    lede: '商汤眼镜故事材料（复制自 SmartGlassInterview）。与 Nirva 题库分栏；音频口径见专栏 README。',
  },
  algolab: {
    title: '专栏 · AlgoLab',
    lede: 'AxiLab / 算法工程化面试材料（来自父目录 algo_lab）。与 Nirva 题库分栏，勿混 ID。',
  },
}

export function ColumnPage() {
  const { columnKey = 'smartglass', docId } = useParams()
  const meta = META[columnKey] ?? {
    title: `专栏 · ${columnKey}`,
    lede: '独立栏目文档（Markdown + Mermaid）。',
  }
  const [docs, setDocs] = useState<ColumnDocListItem[]>([])
  const [detail, setDetail] = useState<ColumnDocDetail | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setError(null)
    void api
      .listColumn(columnKey)
      .then(setDocs)
      .catch((err: Error) => setError(err.message))
  }, [columnKey])

  useEffect(() => {
    if (!docId) {
      setDetail(null)
      return
    }
    setError(null)
    void api
      .getColumnDoc(columnKey, docId)
      .then(setDetail)
      .catch((err: Error) => setError(err.message))
  }, [columnKey, docId])

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Column</p>
        <h1>{meta.title}</h1>
        <p className="lede">{meta.lede}</p>
      </header>
      {error && <p className="error-text">{error}</p>}

      <div className="column-layout">
        <aside className="card column-nav">
          <h2>目录</h2>
          {docs.length === 0 ? (
            <p className="muted small">
              暂无文档。请运行：
              <code>python -m app.import_content</code>
            </p>
          ) : (
            <ul className="stack-list">
              {docs.map((d) => {
                const stem = d.id.includes(':') ? d.id.split(':').slice(1).join(':') : d.id
                return (
                  <li key={d.id}>
                    <Link
                      to={`/column/${columnKey}/${encodeURIComponent(stem)}`}
                      className={docId === stem || docId === d.id ? 'active-doc' : ''}
                    >
                      {d.title}
                    </Link>
                    <span className="muted small" style={{ display: 'block' }}>
                      {stem}
                    </span>
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
              <p className="muted small">
                {detail.filename} · {detail.source_path}
              </p>
              <MarkdownView markdown={detail.body_md} />
            </>
          )}
        </section>
      </div>
    </div>
  )
}
