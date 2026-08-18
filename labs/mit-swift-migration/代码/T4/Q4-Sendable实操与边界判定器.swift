// T4-Q4 Sendable 实操收账 + 边界判定器（挂载体 4.4 本体，T3 遗留观察项 1 回收）
// 段一：OC 时代的 NSLock + 字典缓存标 @unchecked Sendable，在两个 actor 间往返读写；
//       再写 actor 包装版对照两边代码形态。
// 段二：把 C5 的边界判定编码成纯函数，assert 判例。
// 担保注释（C3 纪律三连的实操）：
//   LegacyCache 标 @unchecked Sendable 的理由——
//   ①先问能不能值化：不能，这是跨任务共享的可变缓存，值化等于人人一份、缓存失效；
//   ②再问能不能 actor 化：本例可以（见对照版），但 OC 存量代码改造成本高，此处演示担保路线；
//   ③担保内容：所有可变状态（storage）只经 lock 保护的方法访问，全 API 锁协议自洽，
//     无锁外访问路径、无把内部可变引用泄漏出去的方法——并发可变访问不存在，人肉担保成立。
// 撞墙记录：判定器第一版把 ③④⑤ 全写成 .combine——跟 C5 口述的一边倒押题完全同款。
// 教练追问「③不需要流算子时 TaskGroup 不行吗」后改成分轴判定：先问要不要流算子、再问消费侧形态。
// 教训：押题押出惯性，判定器把病照得清清楚楚——口述与代码互为证据，两边一起错、一起改。
import Foundation

// ---- 段一 A：@unchecked 路线（OC 遗产形态）----
final class LegacyCache: @unchecked Sendable {
    private let lock = NSLock()
    private var storage: [String: String] = [:]

    func read(_ key: String) -> String? {
        lock.lock(); defer { lock.unlock() }
        return storage[key]
    }
    func write(_ key: String, _ value: String) {
        lock.lock(); defer { lock.unlock() }
        storage[key] = value
    }
}

actor Writer {
    let cache: LegacyCache
    init(_ c: LegacyCache) { cache = c }
    func put(_ k: String, _ v: String) { cache.write(k, v); print("  [Writer] 写入 \(k)=\(v)") }
}
actor Reader {
    let cache: LegacyCache
    init(_ c: LegacyCache) { cache = c }
    func peek(_ k: String) -> String? { cache.read(k) }
}

// ---- 段一 B：actor 化对照（不用 @unchecked）----
actor SafeCache {
    private var storage: [String: String] = [:]
    func read(_ key: String) -> String? { storage[key] }
    func write(_ key: String, _ value: String) { storage[key] = value }
}

let legacy = LegacyCache()
let writer = Writer(legacy)
let reader = Reader(legacy)

await writer.put("token", "abc123")                    // actor A 写
let got = await reader.peek("token")                   // actor B 读——跨域往返
assert(got == "abc123", "@unchecked 路线跨域往返应读到值")
print("@unchecked 路线往返成功：\(got!)（锁协议自洽，编译器放行，TSan 也不会抓）")

// 压力验证：并发写不撕裂（锁的本职）
await withTaskGroup(of: Void.self) { group in
    for i in 1...10 { group.addTask { await writer.put("k\(i)", "v\(i)") } }
}
let allReadBack = await withTaskGroup(of: Bool.self) { group -> Bool in
    for i in 1...10 { group.addTask { await reader.peek("k\(i)") == "v\(i)" } }
    var ok = true
    for await r in group { ok = ok && r }
    return ok
}
assert(allReadBack, "并发写入后应全部读回")
print("并发 10 写 10 读全对——锁协议在 actor 之间照样自洽")

// actor 化对照：同样的事，调用点多了 await（每次访问是一次 hop）
let safe = SafeCache()
await safe.write("token", "xyz789")
let got2 = await safe.read("token")
print("actor 化对照往返成功：\(got2!)")
print("形态差异：@unchecked 版调用点是普通方法调用（锁在对象内部）；")
print("actor 版每次访问都是 await（隔离域 hop），但不用写担保注释——把证明义务交还给编译器。")

// ---- 段二：边界判定器（C5 口述的代码化）----
enum Need { case singleValue, debouncedInput, multiSourceMerge, continuousStream, timerHeartbeat }
enum Stack: String { case asyncAwait = "async", combine = "Combine", either = "两边皆可，看消费侧" }

// 第一版（一边倒，已被追问打掉）：③④⑤ 全 .combine——留档对照
func chooseStackFirstTry(for need: Need) -> Stack {
    switch need {
    case .singleValue: return .asyncAwait
    case .debouncedInput: return .combine
    case .multiSourceMerge, .continuousStream, .timerHeartbeat: return .combine  // 病灶：见「事件流」就上 Combine
    }
}

// 修正版：判定轴 = ①一次性还是持续性 → ②要不要流算子 → ③消费侧形态
func chooseStack(for need: Need) -> Stack {
    switch need {
    case .singleValue:        return .asyncAwait      // 一次性任务，async 主场
    case .debouncedInput:     return .combine         // debounce 是 Combine 主场算子
    case .multiSourceMerge:   return .either          // 要 combineLatest/merge 走 Combine；只要并发收口 TaskGroup 就够
    case .continuousStream:   return .either          // AsyncStream 可扛；要背压/多订阅/流算子偏 Combine
    case .timerHeartbeat:     return .either          // Timer.publish vs AsyncTimerSequence，看消费侧在哪个世界
    }
}

assert(chooseStack(for: .singleValue) == .asyncAwait)
assert(chooseStack(for: .debouncedInput) == .combine)
assert(chooseStack(for: .multiSourceMerge) == .either)
assert(chooseStack(for: .continuousStream) == .either)
assert(chooseStack(for: .timerHeartbeat) == .either)
// 第一版留档对照：同三个判例暴露一边倒
assert(chooseStackFirstTry(for: .multiSourceMerge) == .combine)
assert(chooseStackFirstTry(for: .timerHeartbeat) == .combine)
print("判定器五例全过；第一版一边倒病灶留档——判定轴：一次性/持续性 → 要不要流算子 → 消费侧形态")
