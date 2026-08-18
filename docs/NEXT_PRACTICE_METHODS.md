# 下一期：结构化输出监督 + Mermaid + SmartGlass 分栏

> 背景：实面中答案组织缺结构/系统性。目标用费曼与西蒙两区 + 盲答对照，把「看过」变成「讲得出」。  
> 分支：`webapp`（本文件随迭代实现）。

## 0. 问题与目标

| 现象 | 目标行为 |
| --- | --- |
| 答案散、无框架 | 强制五层输出：结论 → 机制 → 案例 → 取舍 → 指标/故障 |
| 默读当会了 | **先盲写/盲讲，再揭晓对照** |
| 白板/状态机讲不清 | Markdown **Mermaid** 可渲染，边画边讲 |

## 1. 费曼区（Teach back）

**入口建议**：题库详情旁「费曼练习」、导航独立页 `/practice/feynman`。

流程（对齐 SmartGlass「关键口述」，但接到本站题库 ID）：

1. 选题（或从薄弱题进入）→ **隐藏标准答案**
2. 计时提示（90s / 2min）
3. 用户在结构化表单中输出（必填区）：
   - 结论（一句话）
   - 机制（怎么工作）
   - 案例（真实/缺口话术）
   - 取舍
   - 指标或「为何暂无指标」
4. 提交后才「对照原文」；可勾选五层检查表；保存草稿到 SQLite（`practice_drafts`）
5. 状态：`attempted` → `compared` →（可选）回写题进度 `recited`

**验收**：未提交草稿前不能看答案；提交后 diff/并排对照；刷新草稿仍在。

## 2. 西蒙区（分解 · 反馈环）

西蒙学习法要点：把大目标拆成可练习的子技能，带着反馈反复练。

**入口**：`/practice/simon` 或仪表盘「今日西蒙块」。

设计：

1. **目标树**（种子自综合版）：例如「BLE Ready 能讲清」拆为  
   Ready 定义 / 断连三分类 / 重连预算 / 指标切片
2. 每个子节点绑定：题号 / 白板 / 口述 prompt
3. **反馈环 UI**：练 → 自评（1–5）→ 记录卡点 → 下次只练未过节点
4. 与清单 D1–D7 可选联动（完成子节点可建议勾清单）

**验收**：至少 1 条官方目标树可导入；节点进度独立持久化；仪表盘显示「本周未过节点」。

## 3. Mermaid 渲染（基础设施，优先做）

从 SmartGlass `webapp/src/MermaidBlock.tsx` / Markdown 管线移植：

- 依赖：`mermaid`（+ 现有 `react-markdown`）
- 统一 `MarkdownView`：普通 MD + \`\`\`mermaid 代码块
- 用于：题库答案、白板、后续 SmartGlass 专栏文档
- 主题：浅色站用 `theme: 'neutral'|'default'`，注意 StrictMode 下 id 唯一

**验收**：白板页或一篇含 mermaid 的 MD 能出图；失败时显示错误文本而非白屏。

## 4. SmartGlass 材料：复制分栏 — 可行

**结论：可行。** 推荐「独立栏目 + 复制精选 MD」，不要把两个 JD 混进同一题库 ID 空间。

```
综合版/          # Nirva Founding iOS（现有）
专栏_SmartGlass/ # 从 SmartGlassInterview/综合版 复制进来的文档
  README.md      # 说明：商汤眼镜故事；与 Nirva 口径差异（尤其音频双链路）
  00_… 01_… …
web：导航「专栏」→ 文档浏览器（只读 MD + Mermaid + 可选口述）
```

| 建议迁入 | 原因 |
| --- | --- |
| `01_项目复盘` `08_核心流程` | 项目叙事 + mermaid 流程模板 |
| `02` `10` `11` 语音链路 | AI 可穿戴加分；注意与 Nirva「BLE PCM」口径写清差异 |
| `04_BLE落地` 可对照不重复导入题库 | 避免与 A/B 题号冲突 |
| `07` 冲刺清单 / `09` 自测 | 可作西蒙子树或口述 prompt |
| `13` 水位表 `15` 反冒认 | 补强诚实边界栏目 |
| 慎迁：`03/06/12` Flutter 深挖 | 除非 JD 明确要 Android/Flutter |

**不要做的**：把 Glass 题与 Nirva `A1` 混 ID；不要默认合并两个 webapp 代码仓（本站继续 FastAPI 进度模型，Glass 的 localStorage 口述逻辑可移植）。

导入：扩展 `import_content` 识别 `专栏_SmartGlass/*.md` 为 `doc` 实体，或前端静态读 `public/content`（Glass 的 generate-content 脚本可参考）。

## 5. 建议实现顺序（tickets）

1. **T11** Mermaid + 统一 MarkdownView（题库/白板先受益）
2. **T12** 费曼区：盲答表单 + 对照 + 草稿 API
3. **T13** 西蒙区：目标树种子 + 节点反馈
4. **T14** 复制 SmartGlass 精选 MD → `专栏_SmartGlass/` + 专栏浏览器
5. **T15** 把 Glass「关键口述」prompt 映射到 Nirva 题/白板（可选）

## 6. 本轮已完成

- 分支 `webapp` 已创建并提交学习站骨架（T01–T10）
