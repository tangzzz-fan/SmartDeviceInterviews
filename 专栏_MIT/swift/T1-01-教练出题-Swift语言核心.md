---
title: "T1 教练出题集：Swift 语言核心（值语义/泛型/协议/闭包）"
topics: [learning, swift, coaching, value-semantics, generics]
type: note
date: 2026-08-15
status: draft
origin: chat
---

# T1 教练出题集：Swift 语言核心

> L2 仿真 · 教练 agent 产出。原料：`20_领域/01-iOS开发/Swift/` 五篇（值语义与引用语义工程深入、class与struct对照速览、进阶特性、any与some对照速览、类型擦除）。注：原料笔记在外部库，本目录不可达；教练按库内既有知识重建模型骨架，考点与原料章节一一对应。
> 学员人设：10 年 OC + UIKit，Swift 混编读过、写过简单页面；预期在 PAT、some/any、闭包捕获语义上暴露漏洞（见 [[01-学员人设卡.md]]）。
> 使用纪律：学员卡住按「弱→中→强」逐级给提示，禁止跳级；直接要答案 → 拒答并反问已排除了什么（C1/C2）。

## 一、共识：5 个核心心智模型

| # | 模型 | 一句话骨架 | OC 迁移锚点 |
|---|------|-----------|------------|
| M1 | 值语义 vs 引用语义是「拷贝 vs 共享身份」 | struct 赋值后独立（CoW 延迟拷贝），class 赋值共享同一实例；关键字只是默认倾向，struct 包裸 class 无语义保证 | OC 里一切皆指针共享；Swift 第一次给你「真的拷贝」 |
| M2 | Optional 是枚举，不是「空指针」 | `T?` 即 `Optional<T>`，只有 `.some(T)` 与 `.none` 两个 case；解包是模式匹配 | OC 的 nil 可发消息、靠运行时兜底；Swift 把「可能没有」做成类型，编译期强制面对 |
| M3 | 协议是一等公民，泛型走静态分发 | 协议 + extension 组合优先于继承；泛型调用由编译器按具体类型特化，经 PWT 找实现 | OC 是运行时消息转发；Swift 大部分分发在编译期就钉死 |
| M4 | 类型系统是编译期账本：some 是账本条目，any 是运行时箱子 | `some P` = 编译器知道、调用者不知道的固定具体型；`any P` = 存在容器（3 指针 buffer + VWT + PWT），装箱换动态 | OC 的 `id<Proto>` 最像 `any P`；Swift 没有与 `some` 对应的旧物 |
| M5 | 闭包是捕获环境的一等值，逃逸要付内存代价 | 闭包 = 代码 + 捕获上下文；`@escaping` 声明它活得比调用栈长，捕获的引用要进堆、要防环 | 近似 OC block，但 Swift 默认强捕获 self（block 默认也强，但不显式标注逃逸） |

学员自检要求：合上表复述 M1–M5 并各举一个自己项目里的例子；读不懂 → 按零基规则先补前置。

## 二、争议：专家吵得最凶的 3 个焦点

**D1 struct-first 到底是不是默认正解？**
- 正方最强论据：值语义免共享、易 Sendable、测试无副作用，SwiftUI/并发时代全面偏向 struct；官方 API 设计指南也默认值类型。
- 反方最强论据：大 struct 拷贝成本真实存在（无 CoW 时）；需要身份（`===`）、继承、共享可变状态（缓存、连接、句柄）时硬用 struct 只会造出「伪装成值的引用」或到处传 `inout`。
- 对迁移者的意义：OC 老手最容易犯的错是「一切皆 class」照搬，其次才是矫枉过正全 struct——边界判断才是考点。

**D2 协议导向（POP）该不该取代面向对象（OOP）？**
- 挑战方最强论据（WWDC 2015 以来）：继承树深了脆、协议组合可横向叠加、值类型无共享可变问题，「继承是复用手段里最重的一种」。
- 守方最强论据：UIKit 生态本身建在继承上（UIViewController 家族）；协议无法表达「is-a 身份」与运行时替换（OC 老手靠消息转发做的热替换，POP 给不了）；纯 POP 在深领域建模里也会出现协议爆炸。
- 对迁移者的意义：迁移期是混血——UIKit 壳保留继承，新数据与逻辑层走协议组合，而不是二选一。

**D3 值类型真的能免锁吗？**
- 正方最强论据：值语义拷贝后独立，天然无共享可变；Sendable 检查把「可安全跨隔离域」变成编译期属性，这是 class + 口头保证做不到的。
- 反方最强论据：struct 里藏一个 class 成员就泄漏（M1 红线）；CoW 写路径本身不是线程安全的；大值拷贝在热路径上可能比共享 + 锁更贵。
- 对迁移者的意义：「值类型 = 线程安全」是半句真理，另外半句是「包装引用必须 CoW 或隔离」。

## 三、概念拷问题（6 道，口述通道）

判定标准：能讲出「为什么」并迁移到新场景 = 过；只能复述定义 = 不过。每题配弱/中/强三级提示。

### C1 struct 包 class 的「假值语义」

问题：`struct ViewModel { var cache: NSMutableDictionary }`（或包一个 class 存储盒），`var b = a` 之后改 `b.cache`，`a` 会不会变？为什么？这违背了哪个模型、怎么修？


### C2 为什么带 associatedtype 的协议不能直接当类型用？

问题：`protocol Animal { associatedtype Food; func eat(_ food: Food) }`，为什么 `let zoo: [Animal]` 编译不过？编译器到底在愁什么？说出至少两个层面的困难，以及现代 Swift（5.7+）给了哪两条出路。


### C3 some 与 any：同一个协议两种写法差在哪？

问题：`func make() -> some Animal` 与 `func make() -> any Animal`，调用方拿到的东西有什么本质区别？为什么 SwiftUI 的 `body` 必须是 `some View` 而不是 `any View`？


### C4 Optional 的本质：Swift 为什么不允许「对 nil 发消息」？

问题：OC 里 `[nil doSomething]` 静默返回零值，Swift 里 `nilValue.doSomething()` 直接编译不过。从「Optional 是枚举」出发，解释这个设计差异的因果链，并说出可选链 `a?.b?.c` 脱糖后大致是什么结构。


### C5 @escaping 的本质与 OC block 的差异

问题：什么情况下闭包必须标 `@escaping`？不标会发生什么？为什么逃逸闭包要特别警惕循环引用——和 OC block 的 `__weak typeof(self)` 惯例相比，Swift 少了哪层保护、多了哪层义务？


### C6 mutating 与 let：值类型的「改」为什么需要特殊声明？

问题：为什么 struct 的方法要改自身得标 `mutating`，而 class 不用？`let` 声明的 struct 为什么连 `mutating` 方法都不能调？从 M1 的拷贝语义推导。


## 四、代码任务题（4 道，代码通道，挂项目 1.2/1.4 载体）

判定标准：本机 `swift` CLI 跑通 + 输出符合预期 + 学员逐行能讲 = 过。代码落 `代码/T1/`，输出贴回批改稿。

### Q1 值语义泄漏现形记（挂载体 1.2 前置）

任务：写一个 struct 包 class 存储的最小例子，证明「赋值后两边齐变」的泄漏；然后给出修复。要求用 `print` 输出证明泄漏与修复两种行为。

- 脚手架：`final class Storage { var value: Int }` + `struct Wrapper { var box: Storage }`。

### Q2 手写 CoW 容器（载体 1.2 本体）

任务：实现一个 CoW 的 `MyArray<T>`：内部 class 存储盒 + `isKnownUniquelyReferenced` 判定的写路径。验证：两个变量共享时改一个不触发拷贝，写另一个才拷贝；用 `print` 或断言证明「赋值廉价、写时拷贝」。

- 脚手架：存储盒 class 里放 `var storage: [T]`；写路径封装成 `mutating func append(_:)`。

### Q3 类型安全的迷你解析层（载体 1.4 前置）

任务：定义 `protocol DecodablePayload { associatedtype Output }` 加两三个实现，写一个泛型函数做「输入 → 解码 → 校验 → 返回 Result」的管道；再分别用 `some` 与 `any` 写一个返回解析器的函数，观察编译器行为差异（允许保留一段编译不过的注释版本说明 PAT 的墙）。


### Q4 闭包捕获与循环引用对拍（载体：迁移基本功）

任务：写一个 class 持有 `@escaping` 闭包的场景（如模拟异步回调存进属性），先构造出循环引用（deinit 不打印），再修复（捕获列表），两版运行输出对比证明修复生效。


## 五、验收规则

- 概念通道：6 题全过（允许批改后复攻）；代码通道：4 题全跑通。
- 任一通道未过 → 主题不记过关，缺口进台账（C3/C4）。
- 本文件是题干版：提示梯与评分要点已拆入 `T1-01-教练密卷-Swift语言核心.md`（仅教练分支/coach worktree，学员禁阅）。
