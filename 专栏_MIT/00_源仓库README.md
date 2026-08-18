# MIT-Migration：用 MIT 拷问法攻坚陌生技术

> 一句话：**把「学一门陌生语言/技术/知识点」做成一场有纪律的拷问**——教练出题、学员作答、代码硬验证、台账如实、费曼讲回。不背答案，只建骨架。

## 这个仓库是干什么的（首要目标）

**本仓库的首要目标不是存档某门语言的知识，而是训练「用 MIT 方法学会任何新东西」的能力。** Swift、Python、设计模式、CoreML 是完整示范案例；教练/学员内容分离，是为了让示范可以被亲手重跑。

仓库里目前有三条使用路径：

| 路径 | 做什么 | 适合谁 |
|------|--------|--------|
| **学方法** | 读方法基座 + 一个完整闭环案例 | 第一次接触 MIT 方法的人 |
| **练方法** | 用学员/教练双 worktree 重跑现有线 | 想亲手把 Swift/Python 再学一遍的人 |
| **用方法** | 开一条 `MIT-<主题>-Migration` 新线 | 想用 MIT 方法攻坚自己陌生领域的人 |

> 全量内容索引（按线 / 轮次 / 类型点击直达）：[`00-内容地图.md`](00-内容地图.md)。

- 方法本源与执行纪律：见 [`MIT-Swift-migration/04-方法论基座-MIT三问与测试协议.md`](MIT-Swift-migration/04-方法论基座-MIT三问与测试协议.md)（自包含，无外部依赖）；
- 完整案例一：[`MIT-Swift-migration/`](MIT-Swift-migration/)——十年 OC/UIKit 老手迁移 Swift/SwiftUI/Concurrency/Combine（T1–T6 全部闭环，代码 Swift 6.3.3 实跑）；
- 完整案例二：[`MIT-Python-Migration/`](MIT-Python-Migration/)——同一位学员的 Python 复习线（T1 基础 → T2 线代 → T3 概率论 → T4 PyTorch → T5 算法收束 → T6 async 落地，六轮闭环，代码全实跑；2026-08-17 补 T7–T9 三独立轮：LLM API 客户端与提示工程 / Embedding 与向量检索 / Tokenizer 与 Transformer，出题+密卷+示例批改/费曼+参考代码齐备并实跑验证）；
- 完整案例三：[`MIT-DesignPattern-Migration/`](MIT-DesignPattern-Migration/)——设计模式系统化（六主题；T1–T6 出题 + 密卷 + 24 个 Swift 代码练习 + 示例批改/费曼，**三处齐全**）。
- 完整案例四：[`MIT-CoreML-Migration/`](MIT-CoreML-Migration/)——CoreML 端侧推理（九主题：T1–T6 Swift 主线 + T7 Python 模型创建与转换（coremltools，实跑）/ T8 VisionKit 与系统视觉能力 / T9 C++ + Python + CoreML 集成（造模→编译→C++ 推理闭环实跑，对拍一致）；密卷全量升级为标准结构，**三处齐全**）。

## MIT 方法速览

| 要素 | 做法 |
|------|------|
| **三问结构** | 每主题收敛为「共识五模型 + 争议三焦点 + 拷问题」；模型是能解释现象的最小骨架，争议题考有边界的立场 |
| **双通道** | 概念口述题 + 代码任务题分开判定——只有口述不算过关（C3） |
| **提示分级** | 卡住按「弱→中→强」逐级给提示，禁止跳级、拒绝代答（C1/C2） |
| **硬验证** | 代码必须本机跑通、输出贴回批改稿；「AI 说我懂了」不算数 |
| **台账如实** | 半过必须拆判分点，未过不得写过关，跑不了的如实记「待真机验证」（C4） |
| **费曼写回** | 全过后用自己的话重写一遍（含新旧技术迁移对比小节），被问倒即退回复攻 |

## 这个仓库怎么用

### 入口一：学方法 —— 读一遍完整案例

建议阅读顺序：`00-学习计划`（全局）→ 任一主题的 `T1-01` 出题 → `T1-02` 作答 → `T1-03` 批改 → `T1-04` 费曼。代码直接本机跑：

```bash
cd MIT-Swift-migration/代码/T1
swift Q1-值语义泄漏现形.swift     # 每个文件都是独立顶层脚本
```

读完一个闭环，你看到的不是「Swift 知识」，而是「拷问怎么设计、答案怎么判、卡住怎么提示、台账怎么记」——这套动作才是要带走的东西。

### 入口二：练方法 —— 学员闭卷、教练对照（双 worktree）

两个学习线都已拆成「教练 / 学员」两个分支，各挂一个 worktree（同时存在，不用切分支）：

| 学习线 | 学员目录（闭卷练） | 教练目录（答案与判分） |
|--------|-------------------|----------------------|
| Swift | `.worktrees/swift-student` | `.worktrees/swift-coach` |
| Python | `.worktrees/python-student` | `.worktrees/python-coach` |
| 设计模式 | `.worktrees/dp-student` | `.worktrees/dp-coach` |
| CoreML | `.worktrees/coreml-student` | `.worktrees/coreml-coach` |

学员目录只有骨架 + 题干 + 空 `代码/T{n}/`，**没有密卷、旧作答、批改、费曼与解法代码**。标准循环：

1. 学员目录闭卷作答（每题自评三档：有把握 / 半懂半猜 / 纯猜）+ 代码实跑；
2. 卡住按「弱 → 中 → 强」去教练目录看密卷提示，**看过的级数如实记进作答稿**；
3. 全过一轮后，去教练目录按密卷评分要点自批（过 / 半过拆判分点 / 未过）；
4. 半过/未过复攻销账，全过写费曼稿；
5. 台账自己填（学员版台账已留空）。

角色细则见各线的 `使用说明书-角色指南.md` 与 `学员须知.md`。

### 想直接看教练侧内容？

- 本地已挂好的教练 worktree：`.worktrees/swift-coach`（Swift）与 `.worktrees/python-coach`（Python），直接打开目录即可看到密卷（提示梯 + 评分要点 + 参考答案定位）、旧作答、批改、费曼、解法代码与台账；
- 不想开目录也行，git 直接读：`git show feat/mit-swift-study:MIT-Swift-migration/T1-01-教练密卷-Swift语言核心.md`（Python 同理，分支名换成 `feat/mit-python-study`）；
- 需要知道的事实：教练侧和学员侧的唯一区别是「工作区里有没有答案文件」。同一仓库的 git 历史里全部内容都在，`git show` 永远翻得到——worktree 隔离防的是「顺手可见」，不防刻意翻历史；真要做到物理隔离，需要给学员开一个**从未含过答案**的独立仓库。

### 入口三：用方法 —— 新增一个 MIT 学习方向

见下一节「新增 MIT 学习方向（SOP）」。这是本仓库首要目标的最终落点：把方法搬到你自己的陌生领域。

## 新增 MIT 学习方向（SOP）

配套执行清单：[`_template/新方向启动清单.md`](_template/新方向启动清单.md)（含可打勾步骤与全部命令）。核心流程：

1. **定方向**：明确主题、学员人设（存量知识 + 预期哪里该错）、主题依赖链（最后一个主题收束）。参考现有线的人设卡与 00 主题表。
2. **开教练分支**：`git checkout -b feat/mit-<short>-study main`（`<short>` 用简短英文标识，如 `swift`、`python`）。
3. **建骨架**：复制任一现有线的 `00/01/02/03/04` 五份骨架文档到 `MIT-<主题>-Migration/`，替换人设卡、主题表与项目载体。
4. **出题即拆卷**：每主题在教练分支产两份——`T{n}-01-教练出题-<主题>.md`（题干：共识五模型 + 争议三焦点 + 概念题 + 代码题 + 脚手架）与 `T{n}-01-教练密卷-<主题>.md`（弱/中/强提示 + 评分要点 + 参考答案）。**密卷从第一天起就不进学员分支。**
5. **开学员分支并闭卷化**：`git checkout -b feat/mit-<short>-study-student feat/mit-<short>-study` → `git rm` 全部密卷文件 → 建空 `代码/T{n}/`（.gitkeep）→ 自查 `git -c core.quotepath=false ls-tree -r --name-only HEAD | grep 密卷` 必须为空 → 提交。
6. **挂双 worktree**：`git worktree add .worktrees/<short>-coach feat/mit-<short>-study` 与 `git worktree add .worktrees/<short>-student feat/mit-<short>-study-student`。
7. **跑闭环**：学员闭卷作答 + 代码实跑 → 教练按密卷判分（过 / 半过拆判分点 / 未过）→ 复攻销账 → 费曼写回 → 台账如实（C1–C5）。一个主题闭环再开下一个；前序遗留观察项在后续主题点名回收。
8. **收官归档（可选）**：整线闭环后 `git checkout main && git merge feat/mit-<short>-study`，main 保持只读归档。

## 目录结构与分支布局

```
MIT-Migration/                            ← 主仓库（main 归档 + 分支管理）
├── README.md                             ← 本文件（使用指南）
├── _template/新方向启动清单.md            ← 开新线的执行清单（SOP 配套）
├── MIT-Swift-migration/                  ← 案例一（T1–T6 闭环）
│   ├── 00–05 骨架文档 + 使用说明书-角色指南.md
│   ├── T{n}-01 教练出题（题干版，main/教练/学员分支一致）
│   ├── T{n}-01 教练密卷（main 归档 + 教练分支持有）
│   ├── T{n}-02 作答 / T{n}-03 批改 / T{n}-04 费曼（归档）
│   ├── 代码/T1~T6（旧解法归档；学员分支为空 .gitkeep）
│   └── 项目真机线/（骨架占位）
├── MIT-Python-Migration/                 ← 案例二（T1–T6 闭环，结构同上）
├── MIT-DesignPattern-Migration/          ← 案例三（T1–T6 齐备）
├── MIT-CoreML-Migration/                 ← 案例四（T1–T9 齐备：Swift + Python 造模 + VisionKit + C++ 集成）
└── worktrees（见下表）

分支布局：
  main                                归档：全线全量（教练侧：题干 + 密卷 + 旧产出 + 使用指南）
  feat/mit-swift-study                Swift 教练：密卷 + 旧产出（已推送）
  feat/mit-swift-study-student        Swift 学员：题干 + 空代码目录（已推送）
  feat/mit-python-study               Python 教练：密卷 + 旧产出（已推送）
  feat/mit-python-study-student       Python 学员：题干 + 空代码目录（已推送）
  feat/mit-dp-study                   设计模式教练：密卷 + 旧产出
  feat/mit-dp-study-student           设计模式学员：三处齐全
  feat/mit-coreml-study               CoreML 教练：密卷 + 参考代码 + 示例批改/费曼
  feat/mit-coreml-study-student       CoreML 学员：三处齐全（自律先写后对照）

已挂 worktree：
  .worktrees/swift-coach            → feat/mit-swift-study
  .worktrees/swift-student          → feat/mit-swift-study-student
  .worktrees/python-coach     → feat/mit-python-study
  .worktrees/python-student   → feat/mit-python-study-student
  .worktrees/dp-coach         → feat/mit-dp-study
  .worktrees/dp-student       → feat/mit-dp-study-student
  .worktrees/coreml-coach     → feat/mit-coreml-study
  .worktrees/coreml-student   → feat/mit-coreml-study-student
```

## 纪律红线（失真即重跑）

- 学员全题全对 → 人设失效；
- 代码全靠教练代写也能判过 → 双通道失守；
- 台账把半懂写成过关 → 如实性失守；
- 学员分支出现密卷内容 → 泄漏，该轮作废重跑。

## 当前状态（2026-08-17）

- **Swift 迁移线**：T1–T6 全部闭环；密卷已与题干分家（6 份），教练/学员双分支 + 双 worktree 就绪；真机线执行序列与回收台账见 `MIT-Swift-migration/05-项目真机线迭代计划.md`；
- **Python 复习线**：T1–T6 全部闭环；T7–T9 三独立轮（LLM 企业落地补齐）出题 + 密卷 + 示例批改/费曼 + 12 个参考代码齐备（httpx/重试/熔断、余弦检索/切分/迷你 RAG/召回评估、BPE/自注意力/单层 Transformer，实跑验证）；双分支 + 双 worktree 就绪，学员分支零密卷；
- **设计模式线**：T1–T6 出题 + 密卷 + 24 个 Swift 代码练习（实跑验证）+ 示例批改/费曼齐备，**三处齐全**；待真实开跑；
- **CoreML 线（新）**：T1–T6 出题 + 密卷 + 24 个 Swift 参考脚本（CoreML/Vision/CreateML，本机实跑）+ 示例批改/费曼齐备，**三处齐全**；双分支 + 双 worktree 就绪；
- **首要目标**：各线内容都是「练方法」的器械——先读方法，再重跑一条线，最后开一条自己的新方向，MIT 方法才算真正学会。
