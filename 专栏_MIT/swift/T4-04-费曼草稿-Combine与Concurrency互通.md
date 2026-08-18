---
title: "T4 费曼草稿：Combine 与 Concurrency 互通（学员重写版）"
topics: [learning, swift, combine, concurrency, feynman]
type: note
date: 2026-08-15
status: draft
origin: chat
---

# T4 费曼草稿：我用自己的话讲一遍 Combine

> 全过后费曼写回（流程第四节）。视角：学员第一人称，讲给一个跟我一样的 KVO/通知老手听。
> 判定背书见 [[T4-03-批改与判定-Combine与Concurrency互通.md|T4 批改]]；代码证据在 `代码/T4/`（Swift 6.3.3 实跑）。

## 一、一句话版本

**KVO/通知的世界观是「发了就收、义务靠记性」，Combine 的世界观是「订阅是合同、凭证是命根」：订阅才建立连接、凭证决定寿命（M1），下游有说「慢点」的权利（M2 背压），操作符是装配出来的管道、错误在类型里流转（M3），与 async 各守疆界、桥是双向的（M4），进 SwiftUI 的插座是 will 语义的对象级广播（M5）。**

## 二、五个骨架，逐个讲

### 1. 订阅是合同不是通知：凭证寿命即订阅寿命

这是我栽进去又爬出来的第一坑。通知是广播——注册完不返回值，发出去就完事；Combine 的 `sink` 返回一个 AnyCancellable，**不存住 = 合同当场撕毁**。Q2 的对照组亲手验的：凭证出语句即 deinit、deinit 即 cancel，连 `_ =` 都不算持有——ARC 世界里没名字的对象活不过这一行，订阅凭证也一样。
设计意图复攻时才想通：这不是坑，是把**订阅寿命与持有者寿命绑死**（RAII 式）——逼你在写下 sink 的那一刻回答「这个订阅该活多久」。KVO 的义务是「记得删」（忘删会崩），Combine 把义务翻面成「必须持有」——漏的后果从崩溃降级为静默失效，反而更隐蔽。标准姿势：`store(in: &Set<AnyCancellable>)`，持有者死、全组了结。
T3 的欠条教训在这里续了一集（Q3 桥 A）：continuation 桥里凭证不存，await 直接挂死——**兑现之前桥本身也得活着，凭证寿命是桥的承重墙**。

### 2. 背压：下游有说「慢点」的权利（人设病灶清除记）

「Combine 就是通知的升级版，发了就收」——我首轮原样交了这句话，人设卡的病灶如期发作。复攻时教练没给答案，只追问了我自己的一个疑问：「sink 时也没见让我报数啊，到底谁对？」
答案是都对、但层次不同：Demand 协议真实存在——订阅时 Subscriber 报初始需求，Publisher 只在有需求时发货，需求自下游**逆流而上**。sink 不用报数，是因为它默认替你报了「无界需求：全都要」。所以平时感觉不到背压，不是背压不存在，是便利层默认放弃了这个权利。
与通知的断裂点一句话：通知收不过来是事故（丢或卡）；Combine 的下游有说「慢点」的权利，只是要真用背压得回协议层写自定义 Subscriber。**疑问从病灶变成理解的入口**——这是本轮我最得意的一次复攻。

### 3. 操作符管道：装配声明 + 错误一等公民

操作符链不是执行指令，是**装配声明**——每个操作符返回新 Publisher，链完才开机。两处撞墙给了实感：
- **Failure 是类型参数、沿管道全程流转**：缓存命中想直接回 `Just`，编译两次拒绝——Just 的 Failure 恒为 Never，与管道的 Error 对不上，`setFailureType` 抹平才通。同一天撞两次同款墙，记深了：错误类型也是管道形状的一部分。
- **retry = 重新订阅上游**：Q1 计数打点 #1 失败、#2 成功——前提是 Deferred/Future 在订阅时才执行，retry 才有东西可「重」。顺序有讲究：debounce 在 retry 前（先决定该不该发、再管失败重几次），反过来就是「每个抖动输入都享受三次重试」。debounce 丢中间留最后（Q1 时间线：四条击键只放行一条），throttle 按节拍取样——电梯关门按钮 vs 节流阀。
catch 把错误消化成保底值后管道继续服务后续输入——KVO/通知没有错误通道（出错靠另发一条通知），Combine 把错误做成了管道上的阀门。

### 4. 边界判定：三轴规则 + 双向桥（T3 D1 收口）

首轮我暴露了一边倒的病：③④⑤ 全押 Combine，自述「怀疑自己有病但自查不出来」——Q4 判定器把病照得清清楚楚（第一版 chooseStackFirstTry 留档）。追问打掉后，分界线升级为**三轴判定**：
1. **一次性还是持续性**：一次性单值任务 → async 主场；
2. **要不要流算子**：debounce/combineLatest/merge 这些 AsyncSequence 生态没补齐的 → Combine；只要「并发出去、收口合并」，TaskGroup 就够；
3. **消费侧形态**：持续流/心跳两边皆可（AsyncStream vs Publisher），看消费方活在哪个世界。
桥是双向的：Combine → async 用 `.first()` + continuation 拉平单值（Q3 桥 A，0.21s 兑现）或 `publisher.values` for-await；async → Combine 用 Future/Deferred 包装。
Q3 还撞出一堵意料之外的墙：顶层 await 上下文里 `RunLoop.run` 被拒（unavailable from asynchronous contexts）——**桥不光接数据，还接「调度世界」**，两个世界的驱动方式不能直接混用。

### 5. @Published：will 语义 + 对象级广播（T2 的账还清）

T2 撞过的 will 语义这里复验（Q2 断言：广播发射瞬间读到的还是旧值）。本轮新还的账是**粒度**：每个 @Published 属性变更各广播一次 objectWillChange，通知里没有任何属性信息（只有「对象要变了」）——所以读到该对象任一属性的视图，任一属性变都陪跑重算。这正是 T2 D3「全广播」的机制根源，也是 @Observable 属性级依赖收集的卖点所在。
细粒度逃生口是 `$属性` 单订（属性流互不串门，Q2 验证），但拿到的 cancellable 得自己管——**C1 的义务原样跟过来，两个知识点在「寿命」上会师**。
Subject 选型一条轴：**新订阅者进来要不要立刻拿到当前值快照**——状态语义（搜索文本、登录用户）走 CurrentValueSubject，纯事件（点击）走 PassthroughSubject。@Published ≈ CurrentValueSubject + 写入口。

## 三、争议题我的立场（讲给同行听）

- **D1 Combine 还有没有未来**：收口为三轴判定（见上）。存量 Combine 不会消失、流算子生态仍是独家，但新代码默认 async、只在需要流算子时请 Combine 出场——这是我的迁移期决策规则，已编码进 Q4 判定器。
- **D2 @Observable vs ObservableObject**：机制上 @Observable 赢（属性级 vs 对象级广播，Q2 实锤了全广播的账）；工程上按部署版本与管道需求选——要做防抖/节流管道还得回 Combine（@Observable 无内建 publisher）。对比实验欠着（台账有记），不冒充已验证。
- **D3 全 Combine 化是不是正解**：不站。我的旧病「控制器什么都拿」会换新衣复发成「什么都上流」——治法同 T2：没人共享的状态 @State 就完事，硬上流是把所有权搞散。务实形态：@State + 局部 Combine 管道，关键路径才全流化。

## 四、迁移对比小节（KVO/通知 ↔ Combine，固定骨架）

| 维度 | OC + KVO/通知（旧世界） | Combine（新世界） | 迁移要点 |
|------|------------------------|------------------|---------|
| 连接模型 | 通知：广播发了就收；KVO：注册即挂钩 | 订阅才建立连接，无订阅者不发货 | 「没人在听」时发布方零成本——心智从广播改为合同 |
| 寿命管理 | 手动 removeObserver（忘删会崩） | 凭证必须持有，deinit 即取消（静默失效） | 义务从「记得删」翻面为「必须存」；store(in:) 进 Set 是标准姿势 |
| 流量控制 | 无（收不过来=丢或卡） | Demand 逆流，下游可说「慢点」 | sink 默认无界需求——背压要显式回协议层 |
| 错误通道 | 无（出错另发一条通知） | Failure 是类型参数，沿管道全程流转 | 错误一等公民：retry/catch 是管道阀门，类型全程可查 |
| 重试/防抖 | 手写计时器+状态机（易漏取消） | debounce/throttle/retry 操作符声明 | 顺序敏感：debounce 在 retry 前；retry=重新订阅 |
| 状态 vs 事件 | KVO（状态）/通知（事件）两套机制 | CurrentValue/Passthrough Subject 一以贯之 | 选型轴：要不要当前值快照 |
| 与 UI 集成 | KVO 回调手改 UI | @Published + objectWillChange 驱动 SwiftUI | will 语义 + 对象级广播——两个旧直觉（did/属性级）都反着 |
| 与异步模型关系 | GCD 回调 + KVO 两套世界 | 与 async 各守疆界，双向桥（values/continuation/Future） | 三轴判定选边，桥接处注意调度世界差异（RunLoop vs async） |

## 五、讲完自查

- 每个模型都能举出 `代码/T4/` 里的运行证据：Q1 时间线+计数（debounce/retry/缓存/catch）、Q2 三组打点+0 事件对照组、Q3 双桥对拍、Q4 跨域往返+判定器五例；
- 五处撞墙（Just 类型墙 ×2、removeDuplicates 冒充证据、凭证承重墙、RunLoop 上下文墙）都能讲出「为什么错、怎么对的」；判定器第一版一边倒留档对照——口述与代码互为证据，两边一起错、一起改；
- 还欠着的：自定义 Subscriber 背压实操（Phase 4/T5 收）、@Observable 对比实验（T5 收）、`values` 桥写码（Phase 4.4 收）、Combine 调试体验（T5 收）——台账有记录，不装懂。

## 关联文档

- [[T4-01-教练出题-Combine与Concurrency互通.md|T4 出题集]]
- [[T4-02-学员作答-Combine与Concurrency互通.md|T4 作答]]
- [[T4-03-批改与判定-Combine与Concurrency互通.md|T4 批改与判定]]
- [[00-学习计划.md|学习计划]] — 台账
