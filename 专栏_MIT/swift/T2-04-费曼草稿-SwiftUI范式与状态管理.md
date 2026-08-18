---
title: "T2 费曼草稿：SwiftUI 声明式范式与状态管理（学员重写版）"
topics: [learning, swiftui, feynman]
type: note
date: 2026-08-15
status: draft
origin: chat
---

# T2 费曼草稿：我用自己的话讲一遍 SwiftUI

> 全过后费曼写回（流程第四节）。视角：学员第一人称，讲给一个跟我一样的 OC 老手听。
> 判定背书见 [[T2-03-批改与判定-SwiftUI范式与状态管理.md|T2 批改]]；代码证据在 `代码/T2/`。

## 一、一句话版本

**SwiftUI 里没有「视图对象」，只有「视图描述」：你改状态，框架重算描述、比对差异、落最小更新——UI 永远是状态的函数，你永远不碰 UI 本身。**

## 二、五个骨架，逐个讲

### 1. 视图是值：我戒「拿实例」的过程

十年 UIKit 把我的手训练成「先找引用，再 set 属性」。SwiftUI 把这个动作直接非法化了——不是不让我写，是**没有东西可 set**：视图是 struct 值，body 是函数，框架每次重算都现造一批描述。我 Q1 里手动调了两次 body，打印出四条 init——调几次造几次，连「上一次的视图」都不存在。
给 OC 同行的翻译：想象你的视图不是 UIView，而是 tableView 的 dataSource 方法——你从不指挥 tableView「把第三行改了」，你只回答「第三行是什么」，变化靠数据驱动 reload。SwiftUI 把这个模式从列表推广到整个界面。
**戒断反应**：想写 `view.isHidden = true` 时，强迫自己改写成两问——「哪个状态该变？」「body 读这个状态时长什么样？」答案就是 `@State isHidden` + `if !isHidden`。

### 2. 状态是唯一真理源，重算分三层

状态变 → body 重算 → diff → 最小渲染。这三层我首轮混成了一锅，复攻后才拆开：
- **重算 body** 只是函数再调一遍，造的是 struct 值，无引用计数、无堆大头——**廉价**；
- **diff** 按身份对齐新旧描述，找差异；
- **渲染更新**才碰屏幕，**贵**，且只落差异。
重算范围不是「从根往下全树」，是**依赖图**——谁读过这个状态谁才重算。这跟 UIKit「谁订阅通知谁刷新」同构，只是订阅表框架自动维护。想通这层，「框架凭什么敢频繁重算」就不是问题了：便宜的那步随便做，贵的步骤被裁剪过。

### 3. 状态包装器：别背表，先问所有权

我首轮的病是背了包装器表却不会选型，根子是没把 ARC 的所有权直觉迁移过来。现在的决策三连问：
1. **谁拥有？** 视图自己创建自己用 → @State（值）/ @StateObject（引用）；别人创建我借用 → @ObservedObject / 普通值传递；需要下游可写 → @Binding；跨层共享 → @Environment。
2. **生命周期跟谁？** 跟一次交互 → 局部 @State；跟页面 → 页面级 StateObject；跟 App → 顶层注入。
3. **重算时谁保管存储？** 这是 @StateObject 和 @ObservedObject 的分水岭——视图值每次重算都重新 init，**@StateObject 的初始化表达式只在身份首次出现时执行一次**（框架按身份代管存储），@ObservedObject 里写 `= X()` 等于每帧重建对象。Q2 的模拟实验把这两条路跑出来了：一条三轮 n=1（状态蒸发），一条 1/2/3（状态存活）。

### 4. Result Builder：body 语法的幕后担保人

这是 T1 预告的盲区，撞墙撞明白的。@ViewBuilder 不是什么魔法，就是一组静态方法（buildBlock/buildOptional/buildEither），编译器把我顺序写下的语句翻译成对它们的调用：
- 多段语句 → buildBlock 按个数打包成嵌套类型（**类型不擦除**，我第一版想装数组直接被编译器骂醒）；
- if/else → buildEither(first/second) 成对入口，包进「位置恒定、类型二选一」的容器（SwiftUI 的 `_ConditionalContent`）；
- if 无 else → buildOptional 包成 Optional。
它跟 T1 的 some View 在这里会师：body 返回类型恒定，正是 builder 把任意分支组合收敛成确定静态类型的结果。**builder 是 some View 的担保人**——这句话是我这轮最得意的总结。

### 5. 生命周期与 Identity：旧钩子没有了，新规则是「身份」

viewDidLoad 没有直系后代。onAppear 是**出现事件**不是对象钩子：导航来回会重触发、重算不触发、没有「页面对象」可言。拉数据首选 `.task`——面子是能直接写 async，里子是**视图消失自动取消任务**；onAppear + 手动 Task {} 等于把结构化并发的安全带解开。
Identity 是 T1 欠的账，这轮还清了：diff 对齐靠身份，身份有**结构**（类型+位置）与**显式**（.id/ForEach id）两种。AnyView 之所以伤性能，不是玄学，是把类型信息擦了、身份系统残了、diff 被迫退化成内容比较。`.id()` 改值 = 换视图：@State 重置、转场按增删走、子树重建——列表里改一行的 id，那行的输入框内容就凭空蒸发。

## 三、争议题我的立场（讲给同行听）

- **D1 混编**：不站队全替换。新页面、状态密集页走纯 SwiftUI；富文本/地图/精细列表控制留 UIKit 壳，`UIHostingController` 桥接，桥接层收敛在一处——这就是我迁移期会画的架构图。
- **D2 状态放哪**：@State-first。OC 老手最大的惯性是「搞个 Manager 什么都装」（Q4 初稿我就犯了：visitCount 也塞 model），治法就是选型三连问的第一问——没人共享的状态上升一层都是污染。
- **D3 ObservableObject vs @Observable**：机制上 @Observable 赢（属性级依赖 vs 对象级 objectWillChange 全广播），工程上按部署版本选。两套心智都得装脑子里，因为存量代码和新代码会在同一个 App 里共存很久。

## 四、迁移对比小节（OC ↔ SwiftUI，固定骨架）

| 维度 | OC + UIKit（旧世界） | SwiftUI（新世界） | 迁移要点 |
|------|---------------------|------------------|---------|
| 视图本体 | UIView/VC 对象树，init 一次活到 dismiss | struct 值描述，重算一次造一次 | 找引用的手瘾必须戒；dataSource 模式是最近的旧知锚点 |
| 更新方式 | 命令式：拿引用 set 属性，人肉同步 | 声明式：改状态，UI = f(state) | 每个「set 属性」翻译成「状态+分支」 |
| 一致性保障 | 状态与 UI 两份存，靠开发者同步（漏一处即 bug） | 状态唯一真理源，框架自动派生 UI | 命令式的税不再交，但状态放哪变成新的设计决策 |
| 数据观察 | KVO/通知手写注册，did 语义（变更回执） | 依赖自动收集；ObservableObject 是 will 语义（变更预告） | willChange 在**变更前**发——我撞墙验证过，KVO 习惯会骗你 |
| 所有权 | strong/weak 修饰符 + 团队约定 | 状态包装器把「谁拥有/谁读/谁传」写进声明 | ARC 所有权直觉可直接迁移，但要挂到「重算重建」上才通 |
| 生命周期 | 对象钩子：viewDidLoad 一次性 | 事件修饰符：onAppear/task 按出现触发，.task 自动取消 | 「加载」概念消失；取消从手动义务变成框架赠品 |
| 局部刷新 | reloadRows/diffable dataSource 手动编排 | Identity 驱动的自动 diff | 别滥用 AnyView 和乱改 .id，等于亲手砸 diff 的指南针 |
| 语法机制 | 无对应物 | @ViewBuilder（result builder）把语句树翻译成类型 | OC 无锚点，只能撞墙硬学——但学完能反哺理解 some View |

## 五、讲完自查

- 每个模型都能举出自己 `代码/T2/` 里的运行证据（不是背书）；
- 三处撞墙（willChange 时机、builder 装数组、漏单参重载）都能讲出「为什么错、怎么对的」；
- 还欠着的：`.task` 取消的实感（T3 收）、cancellable 生命周期（T4 收）、Q4 渲染真机验证（Phase 2 收）——台账有记录，不装懂。

## 关联文档

- [[T2-01-教练出题-SwiftUI范式与状态管理.md|T2 出题集]]
- [[T2-02-学员作答-SwiftUI范式与状态管理.md|T2 作答]]
- [[T2-03-批改与判定-SwiftUI范式与状态管理.md|T2 批改与判定]]
- [[00-学习计划.md|学习计划]] — 台账
