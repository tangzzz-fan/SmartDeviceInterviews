---
title: "T3 教练出题集：Concurrency（async/await、actor、Sendable、结构化并发）"
topics: [learning, swift, concurrency, coaching, actor]
type: note
date: 2026-08-15
status: draft
origin: chat
---

# T3 教练出题集：Concurrency

> L2 仿真 · 教练 agent 产出。原料：`20_领域/01-iOS开发/Swift/` 五篇（Concurrency深度指南、Concurrency与Actors、Sendable与隔离域工程对照、GCD到async工程深入、GCD与async对照速览）。注：原料笔记在外部库，本目录不可达；教练按库内既有知识重建模型骨架，考点与原料章节一一对应。
> 学员人设：GCD/队列/锁/数据竞争排查是强项（挂靠锚点充足），但预期在「Task{}=GCD 套公式」「actor 可重入」「Sendable 编译期检查」上暴露漏洞（见 [[01-学员人设卡.md]]）。
> 回收项：T1 遗留观察项 3——「寿命判断靠直觉会栽」，本轮 C6 盯 Task 寿命；T2 遗留观察项 1——「.task 取消语义无实感」，本轮 C4/Q2 回收。
> 使用纪律：学员卡住按「弱→中→强」逐级给提示，禁止跳级；直接要答案 → 拒答并反问已排除了什么（C1/C2）。

## 一、共识：5 个核心心智模型

| # | 模型 | 一句话骨架 | OC 迁移锚点 |
|---|------|-----------|------------|
| M1 | await 是挂起不是阻塞 | 等结果时线程被释放回池子，回来时再接着跑；「等」不再付「占一根线程」的税 | 类比「回调版网络请求不占线程干等」，但 await 把回调拉平成了顺序代码——心智上是同步的，成本上是异步的 |
| M2 | 结构化并发：任务有父子树，寿命有边界 | async 函数里创建的任务挂在结构上：父结束子必了结（自动等待或取消），没有「发出去就没人管」的野任务 | GCD 是 dispatch 完就撒手，任务与调用方再无任何关系——这是最根本的心智差 |
| M3 | actor 是可重入的隔离域，不是串行队列 | actor 保证同一时刻只有一段代码在动它的状态；但方法内一遇 await 挂起，**别的调用可以进来**——串行队列则是堵在门口排队 | 串行队列类比能帮入门，但「挂起即让出」这一条必须重写直觉：actor 的锁在 await 处会「松手」 |
| M4 | Sendable 是跨隔离域的编译期安全契约 | 能安全跨越并发域的类型才标 Sendable；可变 class 与捕获环境不明的 closure 默认不放心，编译器替你拦 | OC 世界数据竞争靠 TSan 事后抓、靠人脑事前想；Swift 把它提前成编译期类型属性——「隔离域」从口头约定变成账本 |
| M5 | 取消是协作式传播，不是 kill 开关 | `cancel()` 只是沿任务树插旗子，代码要自己查（`Task.isCancelled`/`checkCancellation`）才会停；结构化任务里旗子自动传给所有子任务 | GCD 没有对应物（DispatchWorkItem.cancel 也是协作式但不传播）；最近似的旧知是 NSOperation 的 isCancelled 检查义务 |

学员自检要求：合上表复述 M1–M5，并各举一个 GCD 旧写法「翻译」成 Concurrency 的例子；读不懂 → 按零基规则先补前置。

## 二、争议：专家吵得最凶的 3 个焦点

**D1 Combine 还有没有未来？async 是否通吃？**
- 正方最强论据（async 派）：单一异步值用 await、序列值用 AsyncSequence，语言一等公民、编译器保驾；Combine 学习曲线陡、调试栈深。
- 反方最强论据（Combine 派）：多路合并、防抖节流、背压这些**流算子**，AsyncSequence 生态至今没补齐；声明式管道在复杂事件流上仍然能打。
- 对迁移者的意义：这是 T4 的预演——本轮只需记住「单值/序列走 async，复杂流算子才考虑 Combine」的分界线在争议中。

**D2 全 actor 化是不是正解？**
- 正方最强论据：actor 把锁义务交给编译器，消灭一整类数据竞争；隔离域清晰、可审计。
- 反方最强论据：actor hop 有真实开销（跨域切换要入队调度）；优先级反转问题（低优任务占着 actor，高优任务排队）；细碎状态全 actor 化会把代码切碎成异步拼图。
- 对迁移者的意义：「无共享可变」优先（值类型/Sendable），真需要共享才上 actor，锁不是第一选项但 actor 也不是唯一选项——边界判断是考点。

**D3 Sendable 严格化：一步到位还是渐进迁移？**
- 挑战方最强论据（严格派）：Swift 6 全量检查一步到位，把历史欠的数据竞争债一次还清，@preconcurrency 是饮鸩止渴。
- 守方最强论据（渐进派）：百万行存量代码一夜全红等于让团队停工还债；`@preconcurrency`、`nonisolated(unsafe)`、模块级渐进才是能落地的路。
- 对迁移者的意义：机制必须懂（编译器到底拦什么），策略按仓库现状定——这正是 OC 混编老手的主场决策。

## 三、概念拷问题（6 道，口述通道）

判定标准：能讲出「为什么」并迁移到新场景 = 过；只能复述定义 = 不过。每题配弱/中/强三级提示。

### C1 Task {} 与 DispatchQueue.global().async 差在哪？

问题：两者看起来都是「把一段代码丢到后台跑」。说出至少三个层面的本质差异，并回答：Task {} 创建的任务，和创建它的 async 上下文之间还剩什么关系？

- 弱提示：GCD 的 block dispatch 出去之后，你还拿得到它的什么？Task 句柄能给你什么（结果？错误？还有一个两个字母的词）？
- 中提示：想想 M2——Task {} 虽然不强制等待，但它继承的上下文里有什么东西会跟着它走（优先级？actor 隔离？）？detached 又砍掉了什么？
- 强提示：三个层面：①结果与错误进入类型系统（可 await 可 throws）vs GCD 全靠出参回调；②继承优先级与执行器上下文 vs GCD block 无此概念；③可取消、可被结构化树管理 vs dispatch 完即失联。
- 评分要点：
  - 死记硬背典型：「Task 是新 GCD。」（套公式，人设卡预告的病）
  - 真懂特征：三层差异讲全，且能说出「继承什么/砍掉什么」在 detached 上的体现；能举出一个「该用 Task 不该 detached」的场景。

### C2 actor 的可重入：串行队列经验哪里骗了你？

问题：actor 方法中间有个 await，挂起期间另一个调用进入同一 actor 并改了状态——这合法吗？为什么 actor 敢这么设计？这和「串行队列里一个 block 没跑完、下一个进不来」差在哪？给出一个会因此出 bug 的场景。

- 弱提示：await 挂起时，actor 的「独占」是继续攥着还是松手了？想想 M3 那句话。
- 中提示：如果 actor 挂起时不松手、死攥着锁，会发生什么更糟的事（提示：网络请求挂 3 秒，整个 actor 堵死）？可重入是代价还是解药？
- 强提示：bug 场景的标准形状：方法前半段读状态 → await（松手）→ 后半段基于「旧读到的值」继续写——挂起前后状态已被别人改过，check-then-act 失效。
- 评分要点：
  - 死记硬背典型：「actor 就是串行队列换了语法。」（人设卡预告的核心病灶）
  - 真懂特征：讲清「挂起即让出、回来恢复执行」，说出可重入是为了避免 actor 内死等 IO；能构造 check-then-act 跨挂起点失效的具体场景。

### C3 Sendable：编译器到底在拦什么？

问题：为什么一个普通的 `class User { var name: String }` 不能随便跨 actor 传？closure 为什么默认也不放心？Sendable 检查的本质在保护什么不变量？`@unchecked Sendable` 是什么性质的操作？

- 弱提示：跨隔离域传一个可变引用，两边的代码同时读写它——这是什么经典事故？编译器提前拦的就是这个。
- 中提示：值类型（全 let 的 struct）为什么天然容易 Sendable？class 要满足什么苛刻条件才可能安全（提示：不可变 + 内部无共享）？closure 的捕获列表里藏着什么编译器无法验证的东西？
- 强提示：不变量 = 「同一时刻只有一个隔离域能碰这块可变状态」。Sendable 是「这个类型跨域传递不会破坏该不变量」的类型级承诺；@unchecked = 人拿脑袋担保、编译器关掉检查——出了事 TSan 见。
- 评分要点：
  - 死记硬背典型：「Sendable 就是线程安全的标记。」（讲不出拦的是跨域传递、说不出 closure 的难处）
  - 真懂特征：能说出「可变引用跨域 = 数据竞争的种子」，解释 closure 捕获不可验证，@unchecked 的风险性质讲到位。

### C4 结构化并发与取消传播：.task 的账这回要算清（T2 遗留回收）

问题：`withTaskGroup` 里派出去的任务和 `Task.detached` 的任务，取消时的命运有何不同？SwiftUI 的 `.task` 修饰符随视图消失「自动取消」，这个取消传到正在 await 的子任务里会发生什么？取消是立刻杀死代码吗？

- 弱提示：回到 M5——cancel 是插旗子。旗子插在谁身上？子任务有没有自己的旗子？
- 中提示：结构化子任务的状态（运行中/已取消）会被父任务感知——父在 group 里等所有子了结才返回；detached 与任何父无关，谁也等不到它。
- 强提示：「自动取消」= 视图消失 → .task 的根任务被 cancel → 旗子沿任务树向下传播 → 每个子任务在下一个检查点（await/checkCancellation）看到旗子自行了结；不检查的代码会跑完——取消从头到尾是协作。
- 评分要点：
  - 死记硬背典型：「.task 消失任务就停了。」（以为 cancel 是 kill，不讲协作式）
  - 真懂特征：讲清「插旗-检查-协作了结」链条；结构化 vs detached 在等待/传播上的差异；能说出「不检查旗子的循环取消不掉」。

### C5 Continuation：回调世界的独木桥

问题：`withCheckedContinuation` 是干什么的？为什么它叫 checked——编译器/运行时在「检查」什么义务？resume 两次和一次都不 resume 分别是什么后果？

- 弱提示：OC 的 completion block 要改成 await，需要一个「把回调接住、等它来、再把值交出去」的桥——桥的两岸各是什么？
- 中提示：continuation 代表的是一次性的「欠条」：值只能兑现一次，且必须兑现。checked 版在这两条违规时分别给你什么（运行时崩 vs 永远挂起+调试警告）？
- 强提示：resume 两次 = 运行时 fatal（同一笔债还两次）；不 resume = 调用方永远挂在 await 上（泄漏+卡死），checked 版会打警告帮你抓。unChecked 版是性能换掉保险丝。
- 评分要点：
  - 死记硬背典型：「continuation 就是把回调包成 async。」（说不出一次性义务与两种违规后果）
  - 真懂特征：「欠条只能兑现一次且必须兑现」讲透，两种后果说对，能对比 OC block 时代「completion 忘回调」的同款病。

### C6 Task 的寿命：谁在强持有它？（T1 寿命直觉回收）

问题：`let task = Task { ... }` 之后把 task 变量置 nil，任务会停止吗？Task 句柄与任务本体是什么关系？`.task` 修饰符里的任务句柄存在哪、谁负责取消？你在 T1 里 unowned 栽过寿命判断——这道题把同样的分析用在 Task 上做一遍。

- 弱提示：句柄是遥控器还是电视机本身？扔了遥控器，电视还开着吗？
- 中提示：任务本体由并发运行时调度持有，句柄只是观察/取消入口；要停得显式 cancel。那么「谁来记得 cancel」就是设计问题——.task 把这件事绑给了谁？
- 强提示：对照 T2 的 .task：句柄由框架按视图身份保管，视图消失框架替你 cancel——把「寿命管理」从人脑挪到身份系统，正是它优于手写 onAppear+Task{} 的地方。
- 评分要点：
  - 死记硬背典型：「task 变量没了任务就没了。」（句柄/本体不分，寿命直觉又栽）
  - 真懂特征：句柄≠本体讲清；置 nil 不停任务、cancel 才停；.task 的保管与取消职责归属讲对，并主动勾连 T1 的寿命教训。

## 四、代码任务题（4 道，代码通道，挂项目 3.1/3.2/3.3 载体）

判定标准：本机 `swift` CLI 跑通 + 输出符合预期 + 学员逐行能讲 = 过。代码落 `代码/T3/`，输出贴回批改稿。顶层 `await` 脚本可直接跑（Swift 5.7+）。

### Q1 回调 → async 迁移（载体 3.1 本体）

任务：写一个 OC 风的回调 API `func fetchUser(id:completion:)`（用 DispatchQueue.asyncAfter 模拟网络延迟），用 `withCheckedContinuation` 把它桥成 async 版；顶层 await 调用并打印时间线，证明「等待期间没被堵死」（await 前后穿插心跳打印，等待期间心跳照常）。

- 脚手架：completion 回调 `(Result<User, Error>) -> Void`；async 版 `func fetchUser(id:) async throws -> User`。
- 评分要点：桥的形状正确（continuation.resume 恰好一次、成功/失败两条路都兑现）；时间线证明挂起不阻塞；能讲清这个模式与 OC「block 传参」的一一对应。

### Q2 可取消的并发下载 Gallery（载体 3.2 本体，T2 取消语义回收）

任务：`withTaskGroup` 并发「下载」5 张图（sleep 模拟），主任务睡 1.2s 后 `group.cancelAll()`。先写**不检查取消**的版本跑一遍（看谁不听话跑完），再在子任务分块循环里加 `try Task.checkCancellation()` 跑第二遍，用「完成数/取消数」两组输出对拍，证明取消是协作式传播。

- 脚手架：子任务 `func download(_ id: Int) async throws -> String`，内部 `for chunk in 1...4 { try await Task.sleep(...); try Task.checkCancellation() }`（修复版）。
- 评分要点：两版输出差异即证据；能讲清「旗子传播到检查点生效」链条（C4）；能说出为什么第一版取消不住。

### Q3 actor 缓存的可重入翻车现场（载体 3.3 前置）

任务：写一个 `actor ImageCache`：`func image(for key:) async -> Data`，缓存未命中时 `await fetch(key)`（sleep 模拟）再存入。并发发起两个相同 key 的请求——先跑第一版，用打点证明**同一个 key 被 fetch 了两次**（挂起期间状态被重入）；再修复（记录 in-flight 的 Task 做去重），二跑证明只 fetch 一次。

- 脚手架：actor 内 `private var cache: [String: Data]` + `private var inFlight: [String: Task<Data, Never>]`（修复版）。
- 评分要点：第一版的重复 fetch 是 C2「check-then-act 跨挂起点失效」的活体标本；修复版讲清「把挂起期间的承诺也存进状态」（in-flight 去重）；能对比 GCD 串行队列版为什么反而没这个病（堵门 vs 让位）。

### Q4 Sendable 关卡（载体 3.3 Sendable）

任务：构造跨 actor 传递场景：①传一个全 let 的 struct（应畅通）；②传一个可变 class（留一段编译不过的注释版本 + 报错摘要，说明编译器在拦什么）；③修复路线二选一：改造成不可变值类型，或保留 class 讲清代价后标 @unchecked Sendable。用 print 证明修复版跨域往返成功。

- 评分要点：编译报错摘要抄录准确（Sendable 相关 diagnostic）；能按 C3 解释编译器拦的是什么不变量；@unchecked 路线必须讲清「人肉担保」的风险，不许默默贴标签。

## 五、验收规则

- 概念通道：6 题全过（允许批改后复攻）；代码通道：4 题全跑通。
- 任一通道未过 → 主题不记过关，缺口进台账（C3/C4）。
- 出题文件不含答案全文，只有评分要点——防止学员拿题集当答案册。
