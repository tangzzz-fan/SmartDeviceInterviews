---
title: "T4 教练出题集：Combine 与 Concurrency 互通（Publisher/操作符、与 async 的边界、SwiftUI 状态联动）"
topics: [learning, swift, combine, concurrency, coaching]
type: note
date: 2026-08-15
status: draft
origin: chat
---

# T4 教练出题集：Combine 与 Concurrency 互通

> L2 仿真 · 教练 agent 产出。原料：`20_领域/01-iOS开发/` 五篇（Combine/深入解析、Combine/与Concurrency辨析、Combine/Combine与async对照速览、SwiftUI/Combine深度集成、SwiftUI/状态-Combine实践）。注：原料笔记在外部库，本目录不可达；教练按库内既有知识重建模型骨架，考点与原料章节一一对应。
> 学员人设：delegate/KVO/通知玩了十年（发布订阅锚点充足），但人设卡预告三病灶：**背压说不出所以然（以为和通知一样「发了就收」）**、**Combine vs async 边界靠猜**、**AnyCancellable 不存导致订阅立刻取消（知识性盲区，没实战踩过）**。
> 回收项：T2 遗留观察项 2——「Q2 埋的钩子：不存 cancellable 订阅立刻取消」，本轮 C1/Q3 回收；T2 遗留观察项 4——「objectWillChange 对象级广播粒度」，本轮 C6 深抠；T3 遗留观察项 1——「@unchecked Sendable 无实操」，本轮 Q4 回收；T3 争议 D1——「Combine vs async 边界」，本轮主战场（绑定载体 4.4）。
> 使用纪律：学员卡住按「弱→中→强」逐级给提示，禁止跳级；直接要答案 → 拒答并反问已排除了什么（C1/C2）。

## 一、共识：5 个核心心智模型

| # | 模型 | 一句话骨架 | OC 迁移锚点 |
|---|------|-----------|------------|
| M1 | 订阅是合同不是通知：cancellable 是合同凭证 | Publisher 不主动推，Subscriber 上门订阅时才建立连接；`sink` 返回的 AnyCancellable 是合同凭证，**不存住 = 合同当场撕毁（订阅立即取消）**；存进 `Set<AnyCancellable>` 并在 deinit/视图消失时统一了结 | 通知是「广播发了就收」，注册完不返回值；Combine 多出来的那个返回值就是命根子——这是 KVO/通知老手最容易漏的手 |
| M2 | 背压：需求逆流而上，不是发了就收 | Subscriber 订阅时先报「我要多少」（Demand），Publisher 按需求供货；下游处理不过来可以少要，上游不能硬塞 | OC 通知/广播没有这个概念（发了就收、收不过来丢或卡）——这是 Combine 与「通知升级版」类比的断裂点 |
| M3 | 操作符是声明式管道装配，错误是一等公民 | 每个操作符返回新 Publisher，链起来是装配声明不是执行指令；`Publisher<Output, Failure>` 的 Failure 是类型参数——错误沿管道显式流转，retry/catch 是管道上的阀门 | KVO/通知无错误通道（出错靠另发一条通知）；操作符链类比「流水线工位」 |
| M4 | Combine 与 async 各守疆界，桥是双向的 | 单值异步任务走 async；持续事件流、多路合并、防抖节流、背压走 Combine。桥：`publisher.values` → AsyncSequence（流变序列）；`.firstValue`/continuation → 单值拉平；async → Combine 用 Future/Deferred | GCD completion block 与 KVO 观察在旧世界本来就是两套东西，新世界的分工只是把它们都升级了 |
| M5 | @Published 是 Combine 进 SwiftUI 的插座，will 语义、对象级广播 | `@Published` 包着 publisher，值变更经 objectWillChange 广播给整个对象——**粒度是对象级不是属性级**；will 语义（变更前发，T2 撞过）；sink 不存 = M1 同款死法 | KVO 是属性级 did 语义；@Published 是对象级 will 语义——两个维度都反着，旧直觉两头都会骗你 |

学员自检要求：合上表复述 M1–M5，并各举一个 KVO/通知旧写法「翻译」成 Combine 的例子；读不懂 → 按零基规则先补前置。

## 二、争议：专家吵得最凶的 3 个焦点

**D1 Combine 还有没有未来？async 是否通吃？（T3 争议延续，本轮收口）**
- 正方最强论据（async 派）：Apple 的投入全在 Concurrency（AsyncSequence、AsyncStream 持续进化），Combine 自 2019 后无实质更新；新代码默认 async 是社区主流。
- 反方最强论据（Combine 派）：debounce/throttle 背压感知、多路 merge/combineLatest、错误在类型里传播重试——这些 AsyncSequence 生态至今没补齐；且存量 Combine 代码不会一夜消失。
- 对迁移者的意义：这是本轮的总纲——要产出**可执行的边界判定规则**（什么样的需求走哪边），不许停在「看情况」。

**D2 @Published/ObservableObject vs @Observable：数据流层要不要彻底换底座？**
- 正方最强论据（@Observable 派）：属性级依赖追踪，objectWillChange 全广播造成的多余重算直接消灭；与 async 协作更自然。
- 反方最强论据（Combine 派）：存量 ObservableObject 体量巨大；@Observable 无内建 publisher，想做防抖/节流管道还得回 Combine；部署版本约束。
- 对迁移者的意义：机制差异（对象级 vs 属性级）必须能讲；选型按部署目标与管道需求定——T2 D3 的延续收口。

**D3 事件流层要不要全 Combine 化？命令式状态混用是不是罪？**
- 挑战方最强论据（纯粹派）：状态全走 publisher，UI 全是流的投影，一处命令式就是架构溃堤。
- 守方最强论据（务实派）：简单 UI 状态上流是过度设计；@State + 局部 Combine 管道、关键路径才全流化，才是能落地的形态。
- 对迁移者的意义：学员人设的「控制器什么都拿」旧病会以「什么都上流」的新形态复发——本题盯防新瓶装旧酒。

## 三、概念拷问题（6 道，口述通道）

判定标准：能讲出「为什么」并迁移到新场景 = 过；只能复述定义 = 不过。每题配弱/中/强三级提示。

### C1 订阅的生命周期：sink 的返回值是什么？（T2 遗留钩子回收）

问题：`publisher.sink { ... }` 返回的 AnyCancellable 是什么性质的东西？不把它存起来会发生什么、为什么？KVO/通知十年，你漏过「存 observer」吗——为什么 Combine 非要设计成「不存就取消」？多个订阅怎么统一了结？


### C2 背压：Combine 和通知到底差在哪？（人设卡预告病灶）

问题：「Combine 就是通知的升级版」这个说法哪里对、哪里断裂？什么是 Demand/背压？Subscriber 说「我要一个」之后，Publisher 是推还是等？下游处理不过来会发生什么——和通知「发了就收」有什么本质不同？


### C3 PassthroughSubject vs CurrentValueSubject：该选哪个？

问题：两种 Subject 的差异是什么（提示：一个没有「现在」）？给三个场景各选一个并说理由：①搜索框文本实时流；②「当前登录用户」；③按钮点击事件。@Published 跟谁更像？


### C4 retry 与 debounce：管道上的阀门怎么拧？（错误一等公民）

问题：`.retry(3)` 到底「重」的是什么——重新执行闭包还是重新订阅上游？retry 之后错误类型变了吗？`.debounce` 对连续事件做了什么，它和 throttle 的差异是什么？管道的 `Failure` 类型参数在 retry/catch 前后怎么流转？


### C5 边界判定：这个需求走 Combine 还是 async？（T3 D1 收口）

问题：给五个需求做判定并给理由：①拉一次用户资料；②搜索框防抖后请求；③多个数据源并发拉取后合并渲染；④WebSocket 持续推送；⑤定时器心跳。判定完之后回答：桥怎么搭——已有的 Combine 管道怎么喂给 async 世界，反过来呢？


### C6 @Published 与 SwiftUI：插座的两头（T2 遗留 4 深抠）

问题：`@Published` 底下是什么（提示：T2 的 Q2 用过它的发射器）？objectWillChange 广播的粒度是什么——改对象上任意一个 @Published 属性，观察方会收到几次通知、知不知道是哪个属性变了？这和 @Observable 的属性级追踪差在哪？sink 一个对象的 $属性 和直接观察对象，寿命管理有何不同？


## 四、代码任务题（4 道，代码通道，挂项目 4.2/4.3/4.4 载体）

判定标准：本机 `swift` CLI 跑通 + 输出符合预期 + 学员逐行能讲 = 过。代码落 `代码/T4/`，输出贴回批改稿。Combine 在 macOS CLI 可直接 import（顶层代码 + RunLoop 或同步 Subject 均可驱动）。

### Q1 防抖+重试+缓存搜索管道（载体 4.2 本体）

任务：模拟搜索框：用 PassthroughSubject 接收输入（快速灌入一串带抖动的关键词，如 "s"/"sw"/"swi"/"swift"），构建管道 `debounce(0.3) → removeDuplicates → flatMap 网络请求（第 1 次失败模拟）→ retry(1) → catch 兜底`，打印每个阶段的事件与时间戳。证明：①debounce 只留最后一次输入；②retry 让失败的请求重新发起（打点计数）；③catch 后管道不死、还能出结果。加一个「缓存字典」：同一关键词第二次命中不发请求。

- 脚手架：`func fakeSearch(_ q: String) -> AnyPublisher<[String], Error>`，内部用计数让首次失败；主体 `let input = PassthroughSubject<String, Never>()`。

### Q2 @Published 数据流（载体 4.3 本体）

任务：`final class SearchStore: ObservableObject`，`@Published var query: String`、`@Published var results: [String]`。CLI 无渲染验证三件事：①sink `$query` 单独订阅，改 query 与改 results 各打点，证明**属性流只收到自己的变化**；②sink `objectWillChange`，改任一属性都收到通知且**通知里没有属性信息**，证明对象级广播粒度；③断言 objectWillChange 在值变更**前**发射（T2 will 语义复验）。最后把订阅存进 `Set<AnyCancellable>`，再演示一次「不存直接 sink」的立刻取消（对照组）。


### Q3 桥接实验：Combine ↔ async 双向过桥（载体 4.4 前置）

任务：双向各搭一座桥并打印时间线。桥 A（流→单值）：把 Q1 的搜索 publisher 用 `.first()` + `withCheckedContinuation`（或 values 的 `for await` 取首值）拉平成 `func searchOnce(_ q:) async throws -> [String]`，顶层 await 调用。桥 B（async→流）：把一个 `async` 轮询函数（每 0.2s 产一个值、共 5 个）包成 AsyncStream，再对比同一消费逻辑用 `Timer.publish + sink` 写一遍——两份输出对拍。

- 脚手架：桥 A 用 continuation 桥（T3 Q1 的复用）；桥 B `AsyncStream { continuation in ... }`。

### Q4 Sendable 实操收账 + 边界判定器（载体 4.4 本体，T3 遗留 1 回收）

任务：两段。段一（收账）：写一个 `final class LegacyCache` 模拟 OC 时代的全局缓存（内部 `NSLock` + 可变字典），标 `@unchecked Sendable` 让它在两个 actor 间往返读写——必须写清担保理由注释（锁协议自洽），并跑通往返打点；再写一段对照：同样场景不用 @unchecked、改用 actor 包一层的版本，对比两边代码形态。段二（判定器）：写一个纯函数 `func chooseStack(for need: Need) -> Stack`，把 C5 的判定规则编码成 switch（Need 枚举：singleValue / debouncedInput / multiSourceMerge / continuousStream / timerHeartbeat），assert 五个判例全过。


## 五、验收规则

- 概念通道：6 题全过（允许批改后复攻）；代码通道：4 题全跑通。
- 任一通道未过 → 主题不记过关，缺口进台账（C3/C4）。
- 本文件是题干版：提示梯与评分要点已拆入 `T4-01-教练密卷-Combine与Concurrency互通.md`（仅教练分支/coach worktree，学员禁阅）。
