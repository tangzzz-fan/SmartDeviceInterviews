import { Link } from 'react-router-dom'
import { COLUMN_LIST } from '../columns/catalog'
import './pages.css'

export function ColumnsHubPage() {
  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Columns</p>
        <h1>专栏总览</h1>
        <p className="lede">
          与 Nirva「综合版」题库分栏存放的加料课包。先选专栏，再按分区阅读——不要从侧栏通读全部文件。
        </p>
      </header>

      <div className="hub-grid">
        {COLUMN_LIST.map((c) => (
          <article key={c.key} className="card hub-card">
            <p className="eyebrow">{c.short}</p>
            <h2>
              <Link to={`/column/${c.key}`}>{c.title}</Link>
            </h2>
            <p className="muted">{c.lede}</p>
            <p className="small">
              <strong>适合：</strong>
              {c.audience}
            </p>
            <ol className="path-list">
              {c.pathHints.map((h) => (
                <li key={h}>{h}</li>
              ))}
            </ol>
            <p>
              <Link className="primary-link" to={`/column/${c.key}/${encodeURIComponent(c.startDoc)}`}>
                从导读开始 →
              </Link>
              {c.tracks && (
                <>
                  {' · '}
                  {c.tracks.map((t, i) => (
                    <span key={t.id}>
                      {i > 0 ? ' · ' : ''}
                      <Link to={`/column/${c.key}?track=${t.id}`}>{t.label}</Link>
                    </span>
                  ))}
                </>
              )}
            </p>
          </article>
        ))}
      </div>

      <section className="card">
        <h2>和主线怎么配合</h2>
        <ul className="muted">
          <li>
            <strong>综合版题库</strong>：Nirva Founding iOS 主线（A/B/C…），进度在本站 SQLite。
          </li>
          <li>
            <strong>Glass</strong>：商汤眼镜故事与双链路口径——口述时勿与 Nirva「BLE PCM」加分项混成同一套。
          </li>
          <li>
            <strong>Algo</strong>：AxiLab / 算法工程化；可跑代码在 <code>labs/algo-engineering-lab</code>。
          </li>
          <li>
            <strong>MIT</strong>：四线 MIT 三问钻；代码在 <code>labs/mit-*-migration</code>。
          </li>
        </ul>
      </section>
    </div>
  )
}
