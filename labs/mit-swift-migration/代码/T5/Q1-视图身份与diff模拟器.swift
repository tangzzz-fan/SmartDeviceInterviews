// T5-Q1 视图身份与 diff 模拟器（挂载体 5.1 概念前置）
// 思路：CLI 无渲染，用纯 Swift 模拟 SwiftUI 的帧循环——body 重算产出新视图树后，
// diff 按 Identity 配对。本模拟器统计四类动作：新增/删除/原地更新/复用命中，
// 「重建代价」= 一次昂贵初始化打点（模拟真实渲染成本），只打计数不冒充帧率。
// 三场景：①稳定 id（后端 id）头部插入；②不稳定 id（下标当 id）同样头部插入；
// ③内容全不变只重排。结论预期：身份漂移把「原地更新」全变成「删除+新建」。
// 诚实声明：真实 SwiftUI 的 diff 还有属性级比较与动画路径，本模型只模拟 id 配对层；
// 真机帧率验证记「待真机验证」（C4 纪律）。
import Foundation

// ---- 行模型：id 是身份证，content 是内容 ----
struct Row: Equatable {
    let id: String
    var content: String
}

// ---- diff 报告 ----
struct DiffReport {
    var inserted = 0, removed = 0, updatedInPlace = 0, reused = 0
    var rebuildCost = 0   // 每次「新建」付出一次昂贵初始化
}

// ---- 迷你 diff：按 id 配对（模拟 SwiftUI 按 Identity 匹配）----
func diff(old: [Row], new: [Row]) -> DiffReport {
    var report = DiffReport()
    let oldById = Dictionary(uniqueKeysWithValues: old.map { ($0.id, $0) })
    var matchedOldIds = Set<String>()
    for row in new {
        if let existing = oldById[row.id] {
            matchedOldIds.insert(row.id)
            if existing.content == row.content {
                report.reused += 1              // 身份在、内容没变：直接复用
            } else {
                report.updatedInPlace += 1      // 身份在、内容变了：原地更新
            }
        } else {
            report.inserted += 1                // 新身份：整行新建（昂贵）
            report.rebuildCost += 1
        }
    }
    for row in old where !matchedOldIds.contains(row.id) {
        report.removed += 1                     // 旧身份找不到：删除
        report.rebuildCost += 1
    }
    return report
}

func printReport(_ name: String, _ r: DiffReport) {
    print("\(name)：新增 \(r.inserted) / 删除 \(r.removed) / 原地更新 \(r.updatedInPlace) / 复用 \(r.reused) → 重建代价 \(r.rebuildCost)")
}

// ---- 数据源：1000 行，模拟后端 id（稳定） ----
func makeRows(stableIds: Bool) -> [Row] {
    (0..<1000).map { i in
        Row(id: stableIds ? "row-\(i)" : "\(i)", content: "内容-\(i)")
    }
}

print("=== 场景① 稳定 id + 头部插入一条 ===")
do {
    let old = makeRows(stableIds: true)
    var new = old
    new.insert(Row(id: "row-new", content: "新来的"), at: 0)   // 头部插入
    printReport("①", diff(old: old, new: new))
    // 预期：新增 1、删除 0、复用 1000 —— 身份证没变，后面 1000 行全复用
}

print("=== 场景② 不稳定 id（下标当 id）+ 同样头部插入 ===")
do {
    let old = makeRows(stableIds: true).map { Row(id: $0.id, content: $0.content) }
    // 模拟「下标当 id」：旧列表 id = 0...999；头部插入后所有行的下标右移 1，
    // 于是新列表里 id = 位置下标（0...1000）——内容还是那些内容，身份跟着位置漂移。
    let oldByIndex = old.enumerated().map { Row(id: "\($0.offset)", content: $0.element.content) }
    var shifted = [Row(id: "0", content: "新来的")]
    for (i, r) in oldByIndex.enumerated() {
        shifted.append(Row(id: "\(i + 1)", content: r.content))
    }
    printReport("②", diff(old: oldByIndex, new: shifted))
    // 撞墙记录：我原本预期这里会是「删光+全建」，实跑却是 1 新增/1000 原地更新/0 复用——
    // id 0...999 在两表里都存在，但内容全错位（每行的内容都变成了上一行的）。
    // 想通了：下标当 id 的第一现场不是重建，是「张冠李戴」——diff 认得身份证、
    // 认错了人：1000 行全部被判内容变更要重渲染，挂在行上的局部状态（选中态/输入态）
    // 还会跟着身份错配到别的行。重建代价没爆、渲染代价爆了，状态正确性也赔进去。
}

print("=== 场景②' 更狠的不稳定：每次渲染重新生成 id（UUID） ===")
do {
    // ForEach 里写 id: UUID() 或 .id(UUID()) 的经典病：每次 body 重算身份全部换新。
    let old = (0..<1000).map { _ in Row(id: UUID().uuidString, content: "内容") }
    let new = (0..<1000).map { _ in Row(id: UUID().uuidString, content: "内容") }
    printReport("②'", diff(old: old, new: new))
    // 预期：内容一个字没变，但 1000 删 + 1000 建 —— 这才是「全删全建」的现场
}

print("=== 场景③ 内容全不变、只重排顺序 ===")
do {
    let old = makeRows(stableIds: true)
    let new = Array(old.reversed())
    printReport("③", diff(old: old, new: new))
    // 预期：复用 1000 —— 身份稳定时重排只是搬家，不是重建
}

print("""

结论（对应 M2/C2）：
- ①与②的唯一差别是 id 策略：稳定身份下「插入一条」成本是 1；下标身份下变成
  1000 行内容错位重渲染（撞墙学到的：下标当 id 的第一现场是张冠李戴，不是重建）。
- ②' 是更烈的形态：每次渲染换 UUID，内容不变也 1000 删 1000 建——身份变 = 推倒重建。
- 这就是 ForEach 必须用稳定数据源 id 的原因——身份证跟着位置/渲染漂移，
  diff 认不出「这是原来那行」，轻则全量重渲染，重则整表重建、局部状态错配。
- 场景③说明：重排本身不贵，贵的是「身份变了」。
""")
