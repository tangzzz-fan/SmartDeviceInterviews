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

- 弱提示：先说 SwiftUI 的视图值在 body 重算后发生了什么——你上次 set 的那个「实例」还在吗？
- 中提示：既然实例不存在，「隐藏」这个意图只能编码成什么？body 重算时框架拿什么来决定显不显示？
- 强提示：对照 M2 的公式 UI = f(state)——把需求改写成「状态 + 依赖该状态的 body 分支」。
- 评分要点：
  - 死记硬背典型：「SwiftUI 用 if 控制显隐。」（会写但说不出为什么没有实例）
  - 真懂特征：讲清「视图值是每次重算现造的临时描述，改它等于改上一帧的尸体」，翻译出 `@State isHidden` + `if !isHidden` 的完整形状，并主动对比 UIKit 写法的差异（改对象 vs 改状态源）。

### C2 状态包装器选型：谁拥有，谁读取，谁传入？

问题：一个列表页依赖 `UserStore`（class，持网络与缓存）和「当前筛选条件」（枚举）。给出每个状态该用哪个包装器、放在哪个视图，并回答两个反诘：①为什么不能全用 @ObservedObject？②@StateObject 与 @ObservedObject 的区别用一句话说——在什么时机、谁负责创建？

- 弱提示：先给每个状态回答「它的生命周期应该跟谁走」——跟一次点击？跟当前视图？跟整个 App？
- 中提示：body 会被反复重算、视图值会反复重建——如果一个包装器在每次 init 时都「重新创建」它包的对象，会发生什么？哪个包装器能保证只创建一次？
- 强提示：@StateObject 的存储和 @State 一样由框架按「视图身份」保管，init 里写 `= UserStore()` 只在首次出现时执行；@ObservedObject 不做这件事，传进来什么就用什么。
- 评分要点：
  - 死记硬背典型：「引用类型用 Observed，值用 State。」（讲不出所有权与重建时机）
  - 真懂特征：筛选条件 → @State（视图私有小状态）；UserStore → 创建它的父视图用 @StateObject、下游用 @ObservedObject 或直接传值；两个反诘都答中「重建时机/所有权」要害。

### C3 body 重算：什么时候算、算多大范围、为什么敢算？

问题：一个页面顶层 `ContentView` 含三个子视图。某个 @State 变了——哪些 body 会重算？重算是不是意味着整棵树推倒重画？为什么框架敢频繁重算（成本上凭什么）？

- 弱提示：重算的是「body 这个函数被重新调用」，还是「屏幕上的像素重画」？这两件事谁决定谁？
- 中提示：视图是值（M1）——新建一个 struct 值的成本是什么量级？真正贵的步骤在哪一步发生，由谁裁剪？
- 强提示：依赖收集只标记「读到过变化状态的视图」，diff 之后未变的子树连 body 都不重调——重算范围是依赖图，不是树形全量。
- 评分要点：
  - 死记硬背典型：「状态变了视图就刷新。」（不区分重算与重画，说不出范围）
  - 真懂特征：区分「重算 body（廉价，造值）→ diff（比对）→ 最小渲染更新（贵）」三层；重算范围由依赖决定而非全树；能说出「视图值是廉价描述」正是框架敢频繁重算的底气。

### C4 if/else 凭什么能写进 body？——Result Builder 的机制（T1 遗留缺口回收）

问题：`@ViewBuilder` 背后的 result builder 到底替你做了什么？为什么 body 里多个视图不用写 return、不用包数组？if/else 两个分支在类型层面分别变成了什么？

- 弱提示：回忆 T1 的 M5——闭包是代码+捕获环境。你的 body 内容本质上是传给了一个什么结构的参数？
- 中提示：result builder 是一组静态方法（buildBlock/buildOptional/buildEither…），编译器把「一段顺序写下来的语句」翻译成对这些方法的调用——试着手动翻译两行。
- 强提示：if/else 翻译成 `buildEither(first:)`/`buildEither(second:)`，两分支被包进同一个 `_ConditionalContent<A, B>` 类型——「位置恒定但类型二选一」，这就是条件分支不断 diff 身份的原因。
- 评分要点：
  - 死记硬背典型：「@ViewBuilder 是 SwiftUI 的语法糖。」（说不出翻译机制）
  - 真懂特征：能现场把一小段 body 手动翻译成 buildBlock 调用；讲清 if/else 两分支的类型形状；能把它与 T1 的 some View 结论接上（body 返回类型恒定正是靠 builder 保证的）。

### C5 生命周期平移：viewDidLoad 去哪了？

问题：OC 里「页面加载完拉一次数据」写在哪？SwiftUI 里对应什么？`onAppear` 与 `.task` 各适合什么场景，关键差异是什么？视图「出现」和「视图值被创建」是同一件事吗？

- 弱提示：先分清 M5 里两件事——对象创建（OC 心智）在 SwiftUI 里还成立吗？视图值什么时候被造出来？
- 中提示：onAppear 的闭包是同步上下文，里面发起异步要靠什么？`.task` 除了能直接写 async，还白送你什么行为？
- 强提示：`.task` 的生命周期绑定视图身份：视图消失自动取消任务（结构化并发的取消传播，T3 深讲）——onAppear + Task {} 手写版没有这个保护。
- 评分要点：
  - 死记硬背典型：「onAppear 就是 viewDidLoad。」（不提重算不重触发、不提取消语义）
  - 真懂特征：讲清 viewDidLoad 与 onAppear 的三点差异（触发时机、与重算的关系、有无对象语义）；`.task` 的自动取消是关键差异；能说出「视图值一直在被重建，但 onAppear 按出现事件触发」不矛盾在哪。

### C6 View Identity：框架怎么认出「这还是那个视图」？（T1-C3 印象分回收）

问题：SwiftUI 靠什么判断 diff 时「旧节点 A = 新节点 A」？两种身份来源各是什么？为什么到处包 AnyView 会伤 diff？`.id()` 改变身份会造成什么后果？

- 弱提示：回到 T1 的 M4——some View 让类型恒定。如果两个「看起来一样位置」的视图类型不同，框架还能对齐吗？
- 中提示：结构身份 = 类型 + 树中位置；if/else 两分支类型不同（C4 结论），切分支时框架认为「旧视图死、新视图生」。AnyView 把所有类型擦成一种，身份还剩什么信息？
- 强提示：`.id(someValue)` 是显式身份——值变了等于「换了一个视图」：状态重置、转场按新增/移除走。用「列表里换 id 触发 cell 重建」的例子验证。
- 评分要点：
  - 死记硬背典型：「AnyView 性能差。」（说不出差在身份对齐这一步）
  - 真懂特征：两种身份（结构/显式）讲清；AnyView 的伤害定位到「类型信息被擦掉、diff 退化」；能推出 .id 变化的三个后果（状态重置/动画重做/视图重建）任一并举例。

## 四、代码任务题（4 道，代码通道，挂项目 2.1/2.3 载体）

判定标准：本机 `swift` CLI 跑通 + 输出符合预期 + 学员逐行能讲 = 过；UI 渲染行为无法 CLI 复现的部分，编译验证 + 逻辑通道实跑，渲染部分如实记「待真机验证」（C4）。代码落 `代码/T2/`，输出贴回批改稿。

### Q1 视图是值现形记（载体 2.1 前置）

任务：写一个带 `print` 打点的子视图 struct，在**无渲染环境**（swift CLI）里手动构造父视图、多次调用 body，用输出证明：①视图值每次都是重新 init 出来的（没有持久实例）；②body 是函数，调几次造几次。输出即证据。

- 脚手架：`struct RowView: View { init(_ tag: Int) { print(...) } }` + 一个父视图在 body 里创建若干 RowView；main 里手动调父视图 body 两次对比输出。
- 评分要点：能讲清「init 打点次数 = 值被造的次数」与 M1 一致；能指出这与 UIKit「init 一次用一辈子」的范式差；不要求渲染。

### Q2 所有权模拟实验：StateObject 凭什么只建一次（载体 2.1 状态选型）

任务：不依赖渲染，写一个最小模拟：视图值会反复重建（用函数模拟「重算」），对比两种存储策略——「每次 init 都新建对象」（模拟 @ObservedObject 被误用来创建）vs「外部按身份保管存储、视图重建不动它」（模拟 @StateObject 的框架代管）。用输出证明前者状态丢失、后者状态存活；再用 ObservableObject + @Published + Combine `sink` 实跑一段，证明 objectWillChange 的发射时机（提示：注意 will 这个词）。

- 脚手架：`final class Counter: ObservableObject { @Published var n = 0 }`；模拟函数 `func render(_ makeStore: ...) ` 连续「重算」三次。
- 评分要点：模拟语义映射正确（谁保管存储 = 谁拥有）；objectWillChange 在**变更前**发射这一反直觉点被实跑抓到；能讲清「为什么 ObservedObject 里写 = 初始化是 bug」。

### Q3 手写一个迷你 ViewBuilder（载体 2.3 前置 + C4 代码化）

任务：自己定义一个 `@resultBuilder`（如 `MiniBuilder`，实现 buildBlock/buildOptional/buildEither），用它构造「条件性内容列表」，打印每个分支产出的类型（`type(of:)`），验证：①多段语句被合成一个整体不用 return；②if/else 两分支走 buildEither 且类型二选一；③if 无 else 走 buildOptional。

- 脚手架：`@resultBuilder enum MiniBuilder { static func buildBlock(...) ... }` + `func build(@MiniBuilder _ content: () -> ...) -> ...`。
- 评分要点：buildBlock 的聚合语义写对；buildEither(first/second) 成对出现；能对照 C4 把这段代码与 SwiftUI 的 `_ConditionalContent` 对上号；编译不过的弯路记录在案更好。

### Q4 命令式页面改写为 SwiftUI（载体 2.1 本体）

任务：给一段「OC 风」的 UIKit 命令式实现（一个设置页：开关、计数、列表三元素，命令式改属性 + target-action），改写成纯 SwiftUI 版本：每个状态选对包装器并在注释里写选型理由（谁拥有/谁读/谁传）；命令式交互全部翻译为状态变更。验收分两段：状态逻辑抽成可 CLI 实跑的部分（如模型层 + objectWillChange 证据）；视图渲染部分 `swiftc -typecheck` 编译验证 + 记「待真机验证」。

- 脚手架：`代码/T2/` 内先落一份 `Q4-UIKit原版参考.swift.txt`（伪代码注释版，不编译），再落 SwiftUI 改写版。
- 评分要点：三元素各选对包装器且理由对得上 M3 三件套；无一处「拿引用改属性」残留；编译通过 + 逻辑实跑 = 硬验证部分成立，渲染诚实记待真机。

## 五、验收规则

- 概念通道：6 题全过（允许批改后复攻）；代码通道：4 题全跑通（Q4 渲染段按 C4 记待真机验证，不冒充）。
- 任一通道未过 → 主题不记过关，缺口进台账（C3/C4）。
- 出题文件不含答案全文，只有评分要点——防止学员拿题集当答案册。
