import { useEffect, useState } from 'react'
import { api, type SkillItem, type SkillLevel, type SnapshotKey } from '../api'
import './pages.css'

const LEVELS: SkillLevel[] = ['能连续讲', '能讲骨架', '只能背概念', '没做过']
const GAPS = ['高', '中', '低']

export function SkillsPage() {
  const [items, setItems] = useState<SkillItem[]>([])
  const [snapshot, setSnapshot] = useState<SnapshotKey>('d1')
  const [error, setError] = useState<string | null>(null)

  async function reload() {
    setItems(await api.skills())
  }

  useEffect(() => {
    void reload().catch((err: Error) => setError(err.message))
  }, [])

  const core = items.filter((i) => i.group_name === 'core')
  const bonus = items.filter((i) => i.group_name === 'bonus')

  function levelOf(item: SkillItem) {
    return snapshot === 'd1' ? item.d1_level : item.d7_level
  }
  function gapOf(item: SkillItem) {
    return snapshot === 'd1' ? item.d1_gap : item.d7_gap
  }
  function evidenceOf(item: SkillItem) {
    return snapshot === 'd1' ? item.d1_evidence : item.d7_evidence
  }

  function renderGroup(title: string, list: SkillItem[]) {
    return (
      <section className="card">
        <h2>{title}</h2>
        <ul className="skill-list">
          {list.map((item) => (
            <li key={item.id}>
              <strong>{item.name}</strong>
              <p className="muted small">{item.prompt}</p>
              <div className="filters row">
                <label>
                  水平
                  <select
                    value={levelOf(item) ?? ''}
                    onChange={(e) => {
                      const value = e.target.value as SkillLevel
                      void api
                        .patchSkill(item.id, { snapshot, level: value })
                        .then(reload)
                    }}
                  >
                    <option value="">未填</option>
                    {LEVELS.map((l) => (
                      <option key={l} value={l}>
                        {l}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  差距
                  <select
                    value={gapOf(item)}
                    onChange={(e) => {
                      void api
                        .patchSkill(item.id, { snapshot, gap: e.target.value })
                        .then(reload)
                    }}
                  >
                    <option value="">未填</option>
                    {GAPS.map((g) => (
                      <option key={g} value={g}>
                        {g}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <label className="field">
                证据（一句话）
                <textarea
                  rows={2}
                  defaultValue={evidenceOf(item)}
                  key={`${item.id}-${snapshot}-${evidenceOf(item)}`}
                  onBlur={(e) => {
                    void api
                      .patchSkill(item.id, { snapshot, evidence: e.target.value })
                      .then(reload)
                  }}
                />
              </label>
              {snapshot === 'd7' && item.d1_level && (
                <p className="muted small">
                  D1：{item.d1_level}
                  {item.d1_gap ? ` / 差距${item.d1_gap}` : ''}
                  {item.d1_evidence ? ` · ${item.d1_evidence}` : ''}
                </p>
              )}
            </li>
          ))}
        </ul>
      </section>
    )
  }

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Skills</p>
        <h1>差距地图自评</h1>
        <p className="lede">D1 先填，D7 再填一遍，对比进步。</p>
      </header>
      {error && <p className="error-text">{error}</p>}
      <div className="day-tabs">
        <button
          type="button"
          className={snapshot === 'd1' ? 'primary' : ''}
          onClick={() => setSnapshot('d1')}
        >
          D1 快照
        </button>
        <button
          type="button"
          className={snapshot === 'd7' ? 'primary' : ''}
          onClick={() => setSnapshot('d7')}
        >
          D7 快照
        </button>
      </div>
      {renderGroup('九维核心', core)}
      {renderGroup('加分项', bonus)}
    </div>
  )
}
