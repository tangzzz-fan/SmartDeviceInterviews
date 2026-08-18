// T2-Q2 所有权模拟实验：StateObject 凭什么只建一次（挂载体 2.1 状态选型）
// 思路：不渲染，用函数模拟「body 重算 → 视图值重建」，对比两种存储策略
// 映射关系：谁保管存储 = 谁拥有。@StateObject ≈ 框架按视图身份代管存储盒；
// @ObservedObject ≈ 外部传进来的引用，视图自己不管创建。
import Combine

final class Counter: ObservableObject {
    @Published var n = 0
    let tag: String
    init(_ tag: String) {
        self.tag = tag
        print("  [init] Counter(\(tag)) 被创建")
    }
}

// 策略 A：模拟「在视图 init 里写 @ObservedObject var store = Counter()」的误用——
// 每次重算（视图重建）都重新执行初始化，对象反复被造
func renderObservedStyle() -> Counter {
    return Counter("A")
}

// 策略 B：模拟 @StateObject——框架按视图身份保管存储盒，只在首次出现时执行初始化
final class FrameworkStorage {
    private var store: Counter?
    func stateObject(_ tag: String) -> Counter {
        if store == nil {
            store = Counter(tag) // 只有第一次走到
        }
        return store!
    }
}

print("=== 策略 A：ObservedObject 被误用来创建 ===")
for round in 1...3 {
    let c = renderObservedStyle() // 每次「重算」都拿到新对象
    c.n += 1
    print("  round \(round): n = \(c.n)")
}
print("证据：三轮 n 永远是 1——上一轮的状态跟着旧对象一起丢了")

print("=== 策略 B：StateObject 框架代管 ===")
let storage = FrameworkStorage()
var held: Counter? // 拿住引用好做断言（CLI 里没有视图树替我们拿）
for round in 1...3 {
    let c = storage.stateObject("B") // 三次拿到的是同一个
    held = c
    c.n += 1
    print("  round \(round): n = \(c.n)")
}
assert(held?.n == 3, "StateObject 语义下状态必须跨重算存活")
print("证据：三轮 n = 1/2/3——存储由身份保管，视图值随便重建")

// ---- 附加实验：objectWillChange 的发射时机 ----
// 撞墙记录：第一版我按 KVO 习惯断言「变更之后才发」，实跑 assert 失败——
// sink 闭包里读到的 n 还是旧值。名字里那个 will 不是装饰：它在写操作"发生前"发。
print("=== objectWillChange 时机实验 ===")
final class TimedCounter: ObservableObject {
    @Published var n = 0
}
let tc = TimedCounter()
var bag = Set<AnyCancellable>() // 存住订阅——不存会立刻取消（细节留给 T4 回收）
var seenAtEmit: [Int] = []
tc.objectWillChange
    .sink { _ in
        seenAtEmit.append(tc.n)
        print("  objectWillChange 发射，此刻 n = \(tc.n)")
    }
    .store(in: &bag)

print("即将变更 n: 0 -> 1")
tc.n = 1
print("变更完成，n = \(tc.n)")
assert(seenAtEmit == [0], "objectWillChange 必须在『变更前』发射（will 语义）")
print("证据：发射时读到旧值 0——willChange = 变更预告，不是变更回执")
