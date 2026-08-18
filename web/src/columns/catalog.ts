/** Column browsing catalog: sections, tracks, reading order. */

export type ColumnTrack = {
  id: string
  label: string
  /** stem path prefix, e.g. `swift/` */
  prefix: string
}

export type ColumnMeta = {
  key: string
  title: string
  short: string
  lede: string
  audience: string
  startDoc: string
  tracks?: ColumnTrack[]
  pathHints: string[]
}

export const COLUMN_LIST: ColumnMeta[] = [
  {
    key: 'smartglass',
    title: 'SmartGlass · 商汤眼镜',
    short: 'Glass',
    lede: '项目叙事、双链路口径、冲刺与自测。与 Nirva 题库分栏；音频走 BLE 控制 + WiFi PCM。',
    audience: '智能眼镜 / 语音链路面试加分',
    startDoc: 'README',
    pathHints: [
      '先读 README → 00/01 项目叙事',
      '再练 08 流程 + 10 双链路口径',
      '考前过 07 冲刺与 09 自测',
    ],
  },
  {
    key: 'algolab',
    title: 'AlgoLab · 算法工程化',
    short: 'Algo',
    lede: 'AxiLab 向：面试 Prep、数值一致性 Lab 文档、K3 笔记。代码在 labs/algo-engineering-lab。',
    audience: '穿戴算法落地 / CoreML / OTA DFU',
    startDoc: 'README',
    pathHints: [
      'README → prep/ 面试深挖',
      'lab-docs/ 规范与对齐口径',
      'talk-k3/ 岗位与题集',
    ],
  },
  {
    key: 'mit',
    title: 'MIT Migration · 四线攻坚',
    short: 'MIT',
    lede: 'MIT 三问（出题→作答/密卷→批改→费曼）。四线：Swift / Python / CoreML / Design Pattern。',
    audience: '栈迁移与快速补齐',
    startDoc: 'README',
    tracks: [
      { id: 'swift', label: 'Swift', prefix: 'swift/' },
      { id: 'python', label: 'Python', prefix: 'python/' },
      { id: 'coreml', label: 'CoreML', prefix: 'coreml/' },
      { id: 'designpattern', label: '设计模式', prefix: 'designpattern/' },
    ],
    pathHints: [
      '先看 00-内容地图 / README',
      '选一条轨道：读 00 学习计划',
      '按 T1→Tn 做：出题→作答→批改→费曼',
    ],
  },
]

export function getColumnMeta(key: string): ColumnMeta | undefined {
  return COLUMN_LIST.find((c) => c.key === key)
}

export function stemOf(docId: string): string {
  return docId.includes(':') ? docId.split(':').slice(1).join(':') : docId
}

/** Short sidebar label from filename / stem (not long H1). */
export function navLabel(stem: string, filename: string, title: string): string {
  const base = filename.replace(/\.md$/i, '')
  // MIT drill files: T1-01-教练出题-主题 → T1 · 出题
  const mit = base.match(
    /^T(\d+)-(\d+)-(教练出题|教练密卷|学员作答|批改与判定|费曼草稿)(?:-(.+))?$/,
  )
  if (mit) {
    const role =
      {
        教练出题: '出题',
        教练密卷: '密卷',
        学员作答: '作答',
        批改与判定: '批改',
        费曼草稿: '费曼',
      }[mit[3]] ?? mit[3]
    const topic = mit[4] ? ` · ${mit[4]}` : ''
    return `T${mit[1]} ${role}${topic}`
  }
  // Glass / numbered: 01_项目复盘 → 01 项目复盘
  const numbered = base.match(/^(\d+[A-Za-z]?)[_-](.+)$/)
  if (numbered) return `${numbered[1]} ${numbered[2].replace(/_/g, ' ')}`
  // nested stem last segment
  const leaf = stem.split('/').pop() ?? base
  if (leaf.length <= 28) return leaf
  if (title.length <= 36) return title
  return `${title.slice(0, 34)}…`
}

export type DocSection = {
  id: string
  label: string
  order: number
}

function glassSection(stem: string): DocSection {
  if (stem === 'README' || stem.startsWith('00_')) {
    return { id: 'guide', label: '① 导读', order: 10 }
  }
  if (/^(01_|08_)/.test(stem)) {
    return { id: 'story', label: '② 项目叙事与流程', order: 20 }
  }
  if (/^(02_|04_|10_|11_)/.test(stem)) {
    return { id: 'link', label: '③ 链路与案例', order: 30 }
  }
  if (/^(07_|09_)/.test(stem)) {
    return { id: 'drill', label: '④ 冲刺与自测', order: 40 }
  }
  if (/^(13_|14_|15_)/.test(stem)) {
    return { id: 'edge', label: '⑤ 边界与反问', order: 50 }
  }
  return { id: 'other', label: '其它', order: 90 }
}

function algoSection(stem: string): DocSection {
  if (!stem.includes('/')) {
    return { id: 'root', label: '① 导读与 JD', order: 10 }
  }
  if (stem.startsWith('prep/')) {
    return { id: 'prep', label: '② 面试 Prep', order: 20 }
  }
  if (stem.startsWith('lab-docs/09-CoreML')) {
    return { id: 'coreml-intro', label: '⑤ CoreML 入门', order: 50 }
  }
  if (stem.startsWith('lab-docs/06-实验复盘') || stem.startsWith('lab-docs/06-')) {
    return { id: 'cases', label: '④ 实验复盘', order: 40 }
  }
  if (stem.startsWith('lab-docs/')) {
    return { id: 'lab', label: '③ Lab 规范与口径', order: 30 }
  }
  if (stem.startsWith('talk-k3/')) {
    return { id: 'talk', label: '⑥ Talk with K3', order: 60 }
  }
  return { id: 'other', label: '其它', order: 90 }
}

function mitSection(stem: string): DocSection {
  const parts = stem.split('/')
  if (parts.length === 1) {
    return { id: 'map', label: '① 总览地图', order: 5 }
  }
  const track = parts[0]
  const trackOrder: Record<string, number> = {
    swift: 10,
    python: 20,
    coreml: 30,
    designpattern: 40,
  }
  const trackLabel: Record<string, string> = {
    swift: 'Swift',
    python: 'Python',
    coreml: 'CoreML',
    designpattern: '设计模式',
  }
  const file = parts.slice(1).join('/')
  const baseOrder = (trackOrder[track] ?? 80) * 100
  const tLabel = trackLabel[track] ?? track

  if (/^(00-|01-|02-|03-|04-|05-|README|学员须知|使用说明书)/.test(file)) {
    return { id: `${track}-guide`, label: `${tLabel} · 导读`, order: baseOrder + 10 }
  }
  const tm = file.match(/^T(\d+)/)
  if (tm) {
    const n = Number(tm[1])
    return {
      id: `${track}-t${n}`,
      label: `${tLabel} · T${n}`,
      order: baseOrder + 20 + n,
    }
  }
  return { id: `${track}-other`, label: `${tLabel} · 其它`, order: baseOrder + 90 }
}

export function sectionFor(columnKey: string, stem: string): DocSection {
  if (columnKey === 'smartglass') return glassSection(stem)
  if (columnKey === 'algolab') return algoSection(stem)
  if (columnKey === 'mit') return mitSection(stem)
  const top = stem.includes('/') ? stem.split('/')[0] : 'root'
  return { id: top, label: top, order: 50 }
}

const ROLE_RANK: Record<string, number> = {
  教练出题: 1,
  教练密卷: 2,
  学员作答: 3,
  批改与判定: 4,
  费曼草稿: 5,
}

/** Sort key for curriculum order within a section. */
export function sortKey(stem: string, filename: string): string {
  const base = filename.replace(/\.md$/i, '')
  const mit = base.match(/^T(\d+)-(\d+)-(教练出题|教练密卷|学员作答|批改与判定|费曼草稿)/)
  if (mit) {
    const role = ROLE_RANK[mit[3]] ?? 9
    return `t${mit[1].padStart(2, '0')}-${mit[2]}-${role}`
  }
  const num = base.match(/^(\d+)/)
  if (num) return `n${num[1].padStart(4, '0')}-${stem}`
  if (/README/i.test(base)) return `0-readme`
  if (/^00/.test(base)) return `0-${base}`
  return `z-${stem}`
}

export type GroupedDocs<T extends { id: string; filename: string; title: string }> = {
  section: DocSection
  items: Array<T & { stem: string; label: string }>
}

export function groupColumnDocs<T extends { id: string; filename: string; title: string }>(
  columnKey: string,
  docs: T[],
  trackFilter?: string | null,
): GroupedDocs<T>[] {
  const meta = getColumnMeta(columnKey)
  let list = docs.map((d) => {
    const stem = stemOf(d.id)
    return { ...d, stem, label: navLabel(stem, d.filename, d.title) }
  })

  if (trackFilter && meta?.tracks) {
    const track = meta.tracks.find((t) => t.id === trackFilter)
    if (track) {
      list = list.filter(
        (d) => d.stem.startsWith(track.prefix) || !d.stem.includes('/'),
      )
      // When a track is selected, hide root map docs from the long list? Keep map at top.
    }
  }

  const buckets = new Map<string, GroupedDocs<T>>()
  for (const item of list) {
    const section = sectionFor(columnKey, item.stem)
    let bucket = buckets.get(section.id)
    if (!bucket) {
      bucket = { section, items: [] }
      buckets.set(section.id, bucket)
    }
    bucket.items.push(item)
  }

  for (const b of buckets.values()) {
    b.items.sort(
      (a, b) =>
        sortKey(a.stem, a.filename).localeCompare(sortKey(b.stem, b.filename)) ||
        a.stem.localeCompare(b.stem),
    )
  }

  return [...buckets.values()].sort((a, b) => a.section.order - b.section.order)
}
