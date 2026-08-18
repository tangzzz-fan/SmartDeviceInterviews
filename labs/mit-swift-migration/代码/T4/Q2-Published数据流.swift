// T4-Q2 @Published 数据流（挂载体 4.3 本体，T2 遗留钩子 2 实锤回收）
// 三组打点：①$属性流只收自己的变化（细粒度）；②objectWillChange 对象级广播（无属性信息）；
// ③will 语义断言（变更前发射，T2 Q2 手法复验）。
// 对照组：sink 返回值不存——T2 埋的钩子「不存 cancellable 订阅立刻取消」这回亲手验。
// 撞墙记录：对照组第一版我把 sink 写成一行 `_ = store.$query.sink {...}`，以为赋给 _ 算「处理过」，
// 结果 0 事件——和直接丢掉一模一样。_ 不是持有，临时 AnyCancellable 出语句即 deinit 即 cancel。
// 教训：ARC 世界里「没名字的对象」活不过这一行，订阅凭证也一样。
import Foundation
import Combine

final class SearchStore: ObservableObject {
    @Published var query: String = ""
    @Published var results: [String] = []
}

let store = SearchStore()
var bag = Set<AnyCancellable>()
var queryEvents: [String] = []
var broadcastCount = 0
var willCount = 0

// ① 属性流：只订阅 $query
store.$query
    .dropFirst()   // 跳过订阅时的初始值，只看变化
    .sink { queryEvents.append($0); print("[$query 流] query -> \($0)") }
    .store(in: &bag)

// ②③ 对象级广播 + will 语义打点
store.objectWillChange
    .sink { _ in
        broadcastCount += 1
        willCount = store.query.count + store.results.count   // 发射瞬间读到的「旧值体量」
        print("[objectWillChange] 第 \(broadcastCount) 次广播（无属性信息，只有「要变了」）")
    }
    .store(in: &bag)

print("--- 阶段 1：改 query ---")
let oldLen = store.query.count
store.query = "swift"
assert(broadcastCount == 1, "改一个属性应广播一次")
assert(willCount == oldLen + store.results.count, "will 语义：发射瞬间读到的还是旧值")
assert(queryEvents == ["swift"], "$query 流应收到")
print("断言过：对象级广播 1 次、will 在变更前（读到旧值）、$query 收到自己的变化")

print("--- 阶段 2：改 results（$query 流应无感）---")
store.results = ["a", "b", "c"]
assert(broadcastCount == 2, "另一个属性变更也广播——对象级")
assert(queryEvents == ["swift"], "$query 流不该收到 results 的变化")
print("断言过：任意 @Published 属性变都广播（粒度=对象）；属性流互不串门")

print("--- 阶段 3：对照组——sink 返回值不存 ---")
var ghostEvents = 0
_ = store.$query.dropFirst().sink { _ in ghostEvents += 1 }   // 凭证出语句即释放
store.query = "swiftui"                                        // 变更照常发生
assert(ghostEvents == 0, "不存 cancellable 的订阅应收不到任何事件")
print("断言过：不存凭证 = 订阅当场取消，0 事件——T2 的钩子实锤")
print("而存进 bag 的 $query 流照样收到了 swiftui：\(queryEvents)")
assert(queryEvents == ["swift", "swiftui"], "bag 里的订阅应持续有效")

print("全部断言通过：属性级流 vs 对象级广播 / will 语义 / 不存即取消")
