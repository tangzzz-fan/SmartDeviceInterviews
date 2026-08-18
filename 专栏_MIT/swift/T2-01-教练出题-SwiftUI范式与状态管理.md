---
title: "T2 教练出题集：SwiftUI 声明式范式与状态管理"
topics: [learning, swiftui, coaching, state-management]
type: note
date: 2026-08-15
status: draft
origin: chat
---

# T2 教练出题集：SwiftUI 声明式范式与状态管理

> L2 仿真 · 教练 agent 产出。原料：`20_领域/01-iOS开发/SwiftUI/` 七篇（基础范式转换、状态管理-概览、状态-State与Binding、状态-Observed与StateObject、状态包装器对照速览、UIKit与SwiftUI对比开发、导航对照速览）。注：原料笔记在外部库，本目录不可达；教练按库内既有知识重建模型骨架，考点与原料章节一一对应。
> 学员人设：10 年 OC + UIKit，SwiftUI 一行生产代码没写过，心智停在「视图是对象、命令式改属性」；预期在状态包装器选型、body 重算机制、ViewBuilder 原理、生命周期平移上暴露漏洞（见 [[01-学员人设卡.md]]）。
> 回收项：T1 遗留观察项 1——「Identity/diff 细节是印象分」，本轮 C6 必须回收。
> 使用纪律：学员卡住按「弱→中→强」逐级给提示，禁止跳级；直接要答案 → 拒答并反问已排除了什么（C1/C2）。

## 一、共识：5 个核心心智模型

| # | 模型 | 一句话骨架 | OC 迁移锚点 |
|---|------|-----------|------------|
| M1 | 视图是值，body 是纯函数 | View 是轻量 struct 描述（配置单），不是对象；框架反复调 body 重建描述，你没有任何「实例」可以去 set 属性 | OC 里视图是 UIViewController/UIView 对象树、命令式改属性；SwiftUI 最接近的旧物是「给 tableView 配 dataSource 描述」——描述什么就显示什么，不指挥怎么改 |
| M2 | 状态是唯一真理源，UI = f(state) | 状态变 → body 重算 → 框架 diff 新旧描述 → 只落最小变更；你永远不直接改 UI，只改状态 | 类比 KVO/通知驱动 `[tableView reloadData]`，但依赖收集是框架自动做的，不用你手写观察 |
| M3 | 状态包装器 = 所有权 + 读写权限 + 生命周期 三件套 | @State：框架代管存储、视图私有、跨重算存活；@Binding：借来的读写通道，不拥有；@StateObject：本视图创建并拥有引用型真理源（只建一次）；@ObservedObject：外部拥有、只是传入；@Environment：祖先注入的共享依赖 | 锚点是「谁强持有、谁负责释放」：@StateObject ≈ 自己 lazy 的 strong 属性，@ObservedObject ≈ delegate/外部传入的引用——所有权决定选型 |
| M4 | 重算有范围，Identity 决定 diff | 只有依赖变了的视图才重算；框架靠「结构身份」（在树中的位置/类型）对齐新旧节点，条件分支会改变类型与身份；显式 `.id()` 可改写身份 | 最接近 reload 全量 vs 按 indexPath 局部刷新的 diff 思维；但 SwiftUI 的「indexPath」是类型+位置自动推出来的 |
| M5 | 生命周期是事件修饰符，不是对象钩子 | 没有 viewDidLoad；onAppear/task/onDisappear 挂在视图上按需触发；`.task` 随视图消失自动取消（结构化并发的入口，T3 深讲） | viewDidLoad ≈ onAppear 但不全等：body 每次重算不重触发 onAppear；视图「出现」不等于「对象被创建」（视图值一直在被重建） |

学员自检要求：合上表复述 M1–M5，并各举一个 UIKit 旧代码「翻译」成声明式的例子；读不懂 → 按零基规则先补前置。

## 二、争议：专家吵得最凶的 3 个焦点

**D1 混编是过渡态还是常态？SwiftUI 该不该全面替换 UIKit？**
- 正方最强论据：声明式 + 状态驱动让 UI 代码量与状态同步 bug 断崖式下降；新平台特性（Widget/Vision/Watch）只有 SwiftUI 入口。
- 反方最强论据：UIKit 生态三十年沉淀（富文本、地图、相机、复杂列表精细控制），SwiftUI 每年还在补能力；大型存量 App 全量重写是商业自杀，`UIHostingController`/`UIViewRepresentable` 桥接才是生产现状。
- 对迁移者的意义：这题没有站队答案，考点是「边界判断」——什么页面纯 SwiftUI、什么场景留 UIKit 壳、桥接层怎么收敛。

**D2 全局状态树（单一真理源）vs @State-first 局部状态？**
- 挑战方最强论据（TCA/Redux 一派）：状态集中可预测、可回放、可测试，App 大了之后局部状态散落是灾难。
- 守方最强论据（Apple 官方倾向）：状态应该放在「能覆盖所有依赖它的最小公共祖先」，能 @State 就不上升；全局化一切会把视图私有状态变成公共负担，重算范围反而失控。
- 对迁移者的意义：OC 老手习惯「搞个全局 Manager/单例存状态」，这是本主题最要防的病——先学 @State-first，再谈集中式。

**D3 ObservableObject/@Published 还是 @Observable（Observation 框架）？**
- 正方最强论据（新派）：@Observable 按属性粒度追踪依赖，视图只在真正读到的属性变化时重算；ObservableObject 是对象级 objectWillChange，任意 @Published 变就全体重算。
- 反方最强论据（守旧派）：@Observable 要 iOS 17+，存量 App 最低版本卡死；生态里的教程、第三方库 overwhelmingly 还是 ObservableObject 心智，两套混用团队会精神分裂。
- 对迁移者的意义：机制必须两套都懂（粒度差异正是考点），选型按部署目标定——概念通道拷问机制，不拷问站队。

## 三、概念拷问题（6 道，口述通道）

判定标准：能讲出「为什么」并迁移到新场景 = 过；只能复述定义 = 不过。每题配弱/中/强三级提示。

### C1 「拿到实例改属性」的瘾怎么戒？

问题：UIKit 里 `titleLabel.isHidden = true` 一行搞定，SwiftUI 里为什么没有这行代码的容身之处？把「点击按钮隐藏标题」这个需求翻译成声明式写法，并说清这个翻译背后的因果链（从 M1/M2 推）。


### C2 状态包装器选型：谁拥有，谁读取，谁传入？

问题：一个列表页依赖 `UserStore`（class，持网络与缓存）和「当前筛选条件」（枚举）。给出每个状态该用哪个包装器、放在哪个视图，并回答两个反诘：①为什么不能全用 @ObservedObject？②@StateObject 与 @ObservedObject 的区别用一句话说——在什么时机、谁负责创建？


### C3 body 重算：什么时候算、算多大范围、为什么敢算？

问题：一个页面顶层 `ContentView` 含三个子视图。某个 @State 变了——哪些 body 会重算？重算是不是意味着整棵树推倒重画？为什么框架敢频繁重算（成本上凭什么）？


### C4 if/else 凭什么能写进 body？——Result Builder 的机制（T1 遗留缺口回收）

问题：`@ViewBuilder` 背后的 result builder 到底替你做了什么？为什么 body 里多个视图不用写 return、不用包数组？if/else 两个分支在类型层面分别变成了什么？


### C5 生命周期平移：viewDidLoad 去哪了？

问题：OC 里「页面加载完拉一次数据」写在哪？SwiftUI 里对应什么？`onAppear` 与 `.task` 各适合什么场景，关键差异是什么？视图「出现」和「视图值被创建」是同一件事吗？


### C6 View Identity：框架怎么认出「这还是那个视图」？（T1-C3 印象分回收）

问题：SwiftUI 靠什么判断 diff 时「旧节点 A = 新节点 A」？两种身份来源各是什么？为什么到处包 AnyView 会伤 diff？`.id()` 改变身份会造成什么后果？


## 四、代码任务题（4 道，代码通道，挂项目 2.1/2.3 载体）

判定标准：本机 `swift` CLI 跑通 + 输出符合预期 + 学员逐行能讲 = 过；UI 渲染行为无法 CLI 复现的部分，编译验证 + 逻辑通道实跑，渲染部分如实记「待真机验证」（C4）。代码落 `代码/T2/`，输出贴回批改稿。

### Q1 视图是值现形记（载体 2.1 前置）

任务：写一个带 `print` 打点的子视图 struct，在**无渲染环境**（swift CLI）里手动构造父视图、多次调用 body，用输出证明：①视图值每次都是重新 init 出来的（没有持久实例）；②body 是函数，调几次造几次。输出即证据。

- 脚手架：`struct RowView: View { init(_ tag: Int) { print(...) } }` + 一个父视图在 body 里创建若干 RowView；main 里手动调父视图 body 两次对比输出。

### Q2 所有权模拟实验：StateObject 凭什么只建一次（载体 2.1 状态选型）

任务：不依赖渲染，写一个最小模拟：视图值会反复重建（用函数模拟「重算」），对比两种存储策略——「每次 init 都新建对象」（模拟 @ObservedObject 被误用来创建）vs「外部按身份保管存储、视图重建不动它」（模拟 @StateObject 的框架代管）。用输出证明前者状态丢失、后者状态存活；再用 ObservableObject + @Published + Combine `sink` 实跑一段，证明 objectWillChange 的发射时机（提示：注意 will 这个词）。

- 脚手架：`final class Counter: ObservableObject { @Published var n = 0 }`；模拟函数 `func render(_ makeStore: ...) ` 连续「重算」三次。

### Q3 手写一个迷你 ViewBuilder（载体 2.3 前置 + C4 代码化）

任务：自己定义一个 `@resultBuilder`（如 `MiniBuilder`，实现 buildBlock/buildOptional/buildEither），用它构造「条件性内容列表」，打印每个分支产出的类型（`type(of:)`），验证：①多段语句被合成一个整体不用 return；②if/else 两分支走 buildEither 且类型二选一；③if 无 else 走 buildOptional。

- 脚手架：`@resultBuilder enum MiniBuilder { static func buildBlock(...) ... }` + `func build(@MiniBuilder _ content: () -> ...) -> ...`。

### Q4 命令式页面改写为 SwiftUI（载体 2.1 本体）

任务：给一段「OC 风」的 UIKit 命令式实现（一个设置页：开关、计数、列表三元素，命令式改属性 + target-action），改写成纯 SwiftUI 版本：每个状态选对包装器并在注释里写选型理由（谁拥有/谁读/谁传）；命令式交互全部翻译为状态变更。验收分两段：状态逻辑抽成可 CLI 实跑的部分（如模型层 + objectWillChange 证据）；视图渲染部分 `swiftc -typecheck` 编译验证 + 记「待真机验证」。

- 脚手架：`代码/T2/` 内先落一份 `Q4-UIKit原版参考.swift.txt`（伪代码注释版，不编译），再落 SwiftUI 改写版。

## 五、验收规则

- 概念通道：6 题全过（允许批改后复攻）；代码通道：4 题全跑通（Q4 渲染段按 C4 记待真机验证，不冒充）。
- 任一通道未过 → 主题不记过关，缺口进台账（C3/C4）。
- 本文件是题干版：提示梯与评分要点已拆入 `T2-01-教练密卷-SwiftUI范式与状态管理.md`（仅教练分支/coach worktree，学员禁阅）。
