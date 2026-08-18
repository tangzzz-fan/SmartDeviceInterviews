export type QuestionStatus = 'todo' | 'reviewed' | 'recited'
export type PracticeStatus = 'todo' | 'practiced' | 'mastered'
export type SkillLevel = '能连续讲' | '能讲骨架' | '只能背概念' | '没做过'
export type SnapshotKey = 'd1' | 'd7'

export type QuestionListItem = {
  id: string
  module: string
  priority: string
  title: string
  status: QuestionStatus
  score: number | null
  last_practiced_at: string | null
  orphaned: boolean
}

export type QuestionDetail = QuestionListItem & {
  answer_md: string
  followups_md: string
  tradeoffs_md: string
  source_path: string
  notes: string
}

export type HealthResponse = {
  status: string
  service: string
  database: string
}

export type ModuleStat = {
  module: string
  total: number
  todo: number
  reviewed: number
  recited: number
  weak: number
}

export type DashboardResponse = {
  total: number
  todo: number
  reviewed: number
  recited: number
  modules: ModuleStat[]
  weak_questions: Array<{
    id: string
    title: string
    module: string
    status: QuestionStatus
    score: number | null
  }>
  latest_mock: {
    id: number
    title: string
    round_key: string
    average: number | null
    passed: boolean
  } | null
  open_simon_nodes?: Array<{
    id: string
    goal_title: string
    title: string
    status: string
  }>
}

export type FeynmanChecklist = {
  conclusion: boolean
  mechanism: boolean
  example: boolean
  tradeoff: boolean
  metric: boolean
  followup: boolean
}

export type FeynmanDraft = {
  id: number
  question_id: string
  question_title: string
  conclusion: string
  mechanism: string
  example: string
  tradeoff: string
  metric: string
  checklist: FeynmanChecklist
  status: 'drafting' | 'submitted' | 'compared'
  mark_recited: boolean
  reference_answer_md: string | null
  reference_followups_md: string | null
  reference_tradeoffs_md: string | null
  created_at: string
  updated_at: string
}

export type SimonNodeStatus = 'todo' | 'practicing' | 'passed' | 'stuck'

export type SimonNode = {
  id: string
  goal_id: string
  title: string
  description: string
  linked_question_ids: string[]
  linked_whiteboard_ids: string[]
  sort_order: number
  status: SimonNodeStatus
  self_score: number | null
  blocker_note: string
}

export type SimonGoal = {
  id: string
  title: string
  description: string
  sort_order: number
  nodes: SimonNode[]
  passed_count: number
  total_count: number
}

export type ColumnDocListItem = {
  id: string
  column_key: string
  title: string
  filename: string
  sort_order: number
}

export type ColumnDocDetail = ColumnDocListItem & {
  body_md: string
  source_path: string
}

export type MockScoreItem = {
  id: string
  label: string
  score: number | null
}

export type MockSession = {
  id: number
  title: string
  round_key: string
  scores: MockScoreItem[]
  average: number | null
  passed: boolean
  reflection: string
  created_at: string
  updated_at: string
}

export type ChecklistDay = {
  day_key: string
  day_title: string
  items: Array<{
    id: string
    day_key: string
    day_title: string
    sort_order: number
    text: string
    checked: boolean
  }>
  reflection: string
}

export type WhiteboardItem = {
  id: string
  title: string
  priority: string
  body_md: string
  status: PracticeStatus
  practiced_count: number
  notes: string
}

export type StarItem = {
  id: string
  title: string
  is_flagship: boolean
  body_md: string
  filled_real_numbers: boolean
  recited: boolean
  notes: string
}

export type EnglishItem = {
  id: string
  title: string
  body_md: string
  practiced: boolean
  recording_note: string
}

export type SkillItem = {
  id: string
  name: string
  prompt: string
  criterion: string
  group_name: string
  d1_level: SkillLevel | null
  d1_gap: string
  d1_evidence: string
  d7_level: SkillLevel | null
  d7_gap: string
  d7_evidence: string
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  health: () => request<HealthResponse>('/api/health'),
  dashboard: () => request<DashboardResponse>('/api/dashboard'),
  listQuestions: (params?: {
    module?: string
    priority?: string
    status?: QuestionStatus
  }) => {
    const qs = new URLSearchParams()
    if (params?.module) qs.set('module', params.module)
    if (params?.priority) qs.set('priority', params.priority)
    if (params?.status) qs.set('status', params.status)
    const suffix = qs.toString() ? `?${qs}` : ''
    return request<QuestionListItem[]>(`/api/questions${suffix}`)
  },
  getQuestion: (id: string) => request<QuestionDetail>(`/api/questions/${id}`),
  updateProgress: (
    id: string,
    body: { status?: QuestionStatus; score?: number; notes?: string },
  ) =>
    request<QuestionDetail>(`/api/progress/questions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),

  listMocks: () => request<MockSession[]>('/api/mocks'),
  getMock: (id: number) => request<MockSession>(`/api/mocks/${id}`),
  createMock: (round_key: string, title?: string) =>
    request<MockSession>('/api/mocks', {
      method: 'POST',
      body: JSON.stringify({ round_key, title }),
    }),
  updateMock: (
    id: number,
    body: {
      title?: string
      scores?: MockScoreItem[]
      reflection?: string
    },
  ) =>
    request<MockSession>(`/api/mocks/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  deleteMock: (id: number) =>
    request<{ ok: boolean }>(`/api/mocks/${id}`, { method: 'DELETE' }),

  checklist: () => request<ChecklistDay[]>('/api/checklist'),
  setChecklist: (id: string, checked: boolean) =>
    request(`/api/checklist/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify({ checked }),
    }),
  setReflection: (dayKey: string, findings: string) =>
    request(`/api/reflections/${encodeURIComponent(dayKey)}`, {
      method: 'PUT',
      body: JSON.stringify({ findings }),
    }),

  whiteboards: () => request<WhiteboardItem[]>('/api/whiteboards'),
  patchWhiteboard: (
    id: string,
    body: {
      status?: PracticeStatus
      practiced_count?: number
      notes?: string
      increment?: boolean
    },
  ) =>
    request<WhiteboardItem>(`/api/whiteboards/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),

  stories: () => request<StarItem[]>('/api/stories'),
  patchStory: (
    id: string,
    body: { filled_real_numbers?: boolean; recited?: boolean; notes?: string },
  ) =>
    request<StarItem>(`/api/stories/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),

  english: () => request<EnglishItem[]>('/api/english'),
  patchEnglish: (
    id: string,
    body: { practiced?: boolean; recording_note?: string },
  ) =>
    request<EnglishItem>(`/api/english/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),

  skills: () => request<SkillItem[]>('/api/skills'),
  patchSkill: (
    id: string,
    body: {
      snapshot: SnapshotKey
      level?: SkillLevel
      gap?: string
      evidence?: string
    },
  ) =>
    request<SkillItem>(`/api/skills/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),

  getFeynmanByQuestion: (questionId: string) =>
    request<FeynmanDraft | null>(
      `/api/practice/feynman/by-question/${encodeURIComponent(questionId)}`,
    ),
  saveFeynman: (body: {
    question_id: string
    conclusion?: string
    mechanism?: string
    example?: string
    tradeoff?: string
    metric?: string
    checklist?: FeynmanChecklist
  }) =>
    request<FeynmanDraft>('/api/practice/feynman', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  submitFeynman: (
    id: number,
    body: { mark_recited?: boolean; checklist?: FeynmanChecklist },
  ) =>
    request<FeynmanDraft>(`/api/practice/feynman/${id}/submit`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  resetFeynman: (id: number) =>
    request<FeynmanDraft>(`/api/practice/feynman/${id}/reset`, {
      method: 'POST',
    }),

  listSimon: () => request<SimonGoal[]>('/api/practice/simon'),
  patchSimonNode: (
    id: string,
    body: {
      status?: SimonNodeStatus
      self_score?: number
      blocker_note?: string
    },
  ) =>
    request<SimonNode>(`/api/practice/simon/nodes/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),

  listColumn: (columnKey: string) =>
    request<ColumnDocListItem[]>(`/api/columns/${encodeURIComponent(columnKey)}`),
  getColumnDoc: (columnKey: string, docId: string) =>
    request<ColumnDocDetail>(
      `/api/columns/${encodeURIComponent(columnKey)}/docs/${encodeURIComponent(docId)}`,
    ),
}
