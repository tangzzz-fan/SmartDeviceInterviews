// T6 Q2：@Published ViewModel → @Observable 重构（失效次数对比 + 行为等价对拍）
// 环境：Apple Swift 6.3.3（swift-driver 1.148.6, arm64-apple-macosx26.0），顶层脚本实跑。
// 任务：重构前（ObservableObject + @Published query + @Published private(set) results + $query 管道）
//       vs 重构后（@Observable + 属性级 + withObservationTracking 观察循环），
//       同样「改 query 3 次、改无关属性 3 次」输入：断言新版失效次数严格少于旧版、results 序列等价。
//
// 撞墙记录（如实留档）：
// ① 第一版新版管道想用 $query.debounce——编译不过：@Observable 没有 $ 投影（无内建 publisher，M4 本体）。
//    管道的家改成 withObservationTracking 观察循环（读时追踪代替写时广播）。
// ② 重挂时机第一版放在「计数之后、查新值之前」，重挂瞬间属性还没改，观察闭包立刻又触发一次，
//    计数虚高到 8 次——改「先读新值标 changed、再重挂、变化才计数」（T5 Q4 同步重挂经验的延伸）。
// ③ 旧版 objectWillChange.sink 在 CLI 顶层可用（不需要 receive(on:)），但 @Published 的赋值
//    触发的 objectWillChange 是**写前**发出的——计数语义是「即将失效」不是「已经失效」，
//    与 @Observable 的「读过的依赖变了才回调」不是同一事件点，对比时只看次数不比时序（如实声明）。
// ④ 观察回调里直接 vm.results.append 被 private(set) 拦下（setter 类外不可见）——
//    正解不是放宽 private(set)，而是管道行为收进 VM 自己的方法（recordResult）：保护语义保留，接口不放宽。
// ⑤ 首跑两个真实现场：旧版广播 9 次而非预期 6 次——objectWillChange 把 results 自己的写入也算上了
//    （@Published 全属性广播的账比想的更肥）；新版只收 2 次——探针（/tmp/obs_probe.swift）定位：
//    onChange 在 willSet 时刻同步触发（此刻读属性拿到的还是旧值），回调内读新值永远慢一拍，
//    最后一笔变更的新值没有「下一次变更」来触发落账。修法：回调内只标脏+重挂，新值由
//    「重挂后的 access 读」与「finish() 冲刷」两处落账。学费三笔：objectWillChange 与 onChange
//    都是 will 语义（事件点只比次数不比时序）；一次性回调的落账点在重挂后的读不在回调内的读；
//    观察者寿命要显式了结——不 finish，最后一笔永远悬着（旧世界 cancellable 不会替你翻的账）。

import Combine
import Foundation
import Observation

// MARK: - 重构前：ObservableObject + @Published（旧世界）

final class LegacySearchVM: ObservableObject {
    @Published var query = ""
    @Published private(set) var results: [String] = []   // private(set) 保护语义保留
    @Published var noise = 0                             // 无关属性：陪跑重算的账
    private var cancellables = Set<AnyCancellable>()

    init() {
        // 存量管道：$query → 模拟查询 → results（debounce 在 CLI 的 scheduler 限制下记口述等价，待真机验证）
        $query
            .sink { [weak self] q in
                guard let self else { return }
                guard !q.isEmpty else { return }
                self.results.append("旧(\(q))")
            }
            .store(in: &cancellables)
    }
}

// MARK: - 重构后：@Observable（新世界）

@Observable
final class ModernSearchVM {
    var query = ""
    private(set) var results: [String] = []              // private(set) 保留（C4 直译点）
    var noise = 0

    // 管道的家：查询结果的写入收在 VM 内部（撞墙④：观察回调在类外，碰不到 private(set) 的 setter）
    func recordResult() { results.append("新(\(query))") }
}

// 观察探针：withObservationTracking 一次性回调 + 同步重挂（T5 Q4 探针法的延伸）
// 关键语义（撞墙⑤探针定位）：onChange 在 willSet 时刻触发，回调内读属性拿到的是旧值；
// 因此回调内只标脏，新值在「重挂后的 access 闭包」里读并落账——与 objectWillChange 的 will 语义同事件点。
// @unchecked Sendable 担保：所有读写只发生在创建它的作用域内，无跨隔离域访问
final class QueryObserver: @unchecked Sendable {
    private let vm: ModernSearchVM
    private var lastQuery = ""
    var invalidations = 0
    private var dirty = false

    init(vm: ModernSearchVM) { self.vm = vm }

    func start() { arm() }

    // 显式收尾（撞墙⑤）：will 语义下最后一笔变更的新值没有「下一次变更」来触发落账，
    // finish 冲刷当前新值——观察者的寿命义务，不冲刷则最后一笔永远悬着
    func finish() {
        record(vm.query)
    }

    private func record(_ q: String) {
        guard q != lastQuery else { return }
        dirty = false
        invalidations += 1
        lastQuery = q
        vm.recordResult()                              // 管道行为等价：查询结果落 results（收进 VM 内部）
    }

    private func arm() {
        withObservationTracking {
            // access 闭包：读即追踪；重挂后若属性已变（上一轮 willSet 标脏），新值在这里落账
            let q = vm.query
            if dirty { record(q) }
        } onChange: { [self] in
            dirty = true            // willSet 时刻：此刻读到的还是旧值，只标脏
            arm()                   // 同步重挂：新值由重挂后的 access 闭包落账
        }
    }
}

// MARK: - 对拍驱动：同样的输入序列

func driveLegacy() -> (invalidations: Int, results: [String]) {
    let vm = LegacySearchVM()
    var invalidations = 0
    let c = vm.objectWillChange.sink { _ in invalidations += 1 }   // 对象级广播计数
    for q in ["a", "ab", "abc"] { vm.query = q }                   // 改 query 3 次
    for n in 1...3 { vm.noise = n }                                // 改无关属性 3 次
    c.cancel()
    return (invalidations, vm.results)
}

func driveModern() -> (invalidations: Int, results: [String]) {
    let vm = ModernSearchVM()
    let observer = QueryObserver(vm: vm)
    observer.start()
    for q in ["a", "ab", "abc"] { vm.query = q }                   // 同样的 query 变更（投递是同步 willSet，无需节拍）
    for n in 1...3 { vm.noise = n }                                // 同样的无关变更
    observer.finish()            // 显式收尾（撞墙⑤）：冲刷最后一笔新值，不等脚本退出隐式丢
    return (observer.invalidations, vm.results)
}

let legacy = driveLegacy()
let modern = driveModern()

Swift.print("=== 重构前（ObservableObject）===")
Swift.print("失效次数（objectWillChange 广播）：\(legacy.invalidations)")
Swift.print("results：\(legacy.results)")

Swift.print("\n=== 重构后（@Observable）===")
Swift.print("失效次数（属性级追踪，仅 query）：\(modern.invalidations)")
Swift.print("results：\(modern.results)")

Swift.print("\n=== 判定 ===")
let legacyCount = legacy.invalidations
let modernCount = modern.invalidations
Swift.print("爆炸半径：旧 \(legacyCount) 次 vs 新 \(modernCount) 次（无关属性变更旧版陪跑、新版无感；旧版连 results 自己的写入都广播）")
if modernCount < legacyCount {
    Swift.print("✅ 新版失效次数严格更少——属性级追踪实锤")
} else {
    Swift.print("❌ 失效次数未收敛，查观察循环")
}
let legacyNormalized = legacy.results.map { $0.replacingOccurrences(of: "旧(", with: "(") }
let modernNormalized = modern.results.map { $0.replacingOccurrences(of: "新(", with: "(") }
if legacyNormalized == modernNormalized {
    Swift.print("✅ 行为等价：两版 results 序列一致 \(modernNormalized)")
} else {
    Swift.print("❌ 行为不等价：旧 \(legacyNormalized) vs 新 \(modernNormalized)")
}
Swift.print("\n重构笔记：状态部分直译（@Published → 普通属性，private(set) 保留）；管道的家从 $query 搬到观察循环；")
Swift.print("objectWillChange 是写前「即将失效」、withObservationTracking 是「依赖动过」——事件点不同，对比只比次数不比时序。")
