// T5-Q2 Actor vs 锁基准测试（挂载体 5.4 本体，T3 遗留观察项 2 回收）
// 思路：同一工作负载（字典累加）三实现：actor 版 / NSLock 版 / 无同步单任务基线。
// withTaskGroup 10 并发任务 × 各写 2000 次，测总耗时 + 正确性（== 20000）。
// 追加「细粒度 vs 批量」对照：逐次 await actor 方法 vs 攒一批一次提交——hop 放大效应。
// 纪律：多轮（3 轮）取稳态，第一轮预热数据单列；数字只证明相对关系，
// 绝对微秒数随机器漂移，真机 Instruments 结论记「待真机验证」。
// 撞墙记录①：预热循环写 `for _ in 0...1` 后又在循环体里 `if _ == 1`——编译器当场拒绝：
// `_` 只能出现在模式匹配或赋值左侧，不能在表达式里比较。旧世界写惯了下标循环，
// 想当然把 `_` 当成匿名计数器用，Swift 里匿名就是真匿名，要用就得给名字。
// 撞墙记录②：结论第一版我写「actor vs NSLock 差出几十倍」——实跑数据狠狠打脸：
// hop 放大是数千倍（6346ms vs 0.67ms），而 actor 与 NSLock 本身只差 ~1.3x。
// 且 CLI 解释器开销把每次调用都放大，十几秒干 20000 次增量的绝对值没有推广意义——
// 旧世界「先预设一个结论再找数据」的惯性在这里现形：预设的差距在错的地方。
// 教训：基准跑完先读数据再下笔，测量环境（解释器）必须随结论一起声明。
import Foundation

let rounds = 3
let workers = 10
let perWorker = 2000
let expectedTotal = workers * perWorker

// ---- 实现一：actor 版 ----
actor CounterActor {
    private var counts: [String: Int] = [:]
    func bump(_ key: String) { counts[key, default: 0] += 1 }
    func bumpBatch(_ key: String, times: Int) {          // 批量口：一次 hop 干完一批
        counts[key, default: 0] += times
    }
    func total() -> Int { counts.values.reduce(0, +) }
}

// ---- 实现二：NSLock 版（OC 时代肌肉记忆）----
final class LockCounter: @unchecked Sendable {
    private var counts: [String: Int] = [:]
    private let lock = NSLock()
    func bump(_ key: String) {
        lock.lock()
        counts[key, default: 0] += 1
        lock.unlock()
    }
    func total() -> Int {
        lock.lock()
        defer { lock.unlock() }
        return counts.values.reduce(0, +)
    }
}

func ms(_ d: Duration) -> Double { Double(d.components.seconds) * 1000 + Double(d.components.attoseconds) / 1e12 }

// ---- 跑一轮：返回 (耗时ms, 最终计数) ----
func runActorRound() async -> (Double, Int) {
    let actor = CounterActor()
    let clock = ContinuousClock()
    let start = clock.now
    await withTaskGroup(of: Void.self) { group in
        for w in 0..<workers {
            group.addTask {
                for _ in 0..<perWorker { await actor.bump("w\(w)") }   // 细粒度：每次一跳
            }
        }
    }
    let total = await actor.total()
    return (ms(clock.now - start), total)
}

func runLockRound() async -> (Double, Int) {
    let counter = LockCounter()
    let clock = ContinuousClock()
    let start = clock.now
    await withTaskGroup(of: Void.self) { group in
        for w in 0..<workers {
            group.addTask {
                for _ in 0..<perWorker { counter.bump("w\(w)") }
            }
        }
    }
    return (ms(clock.now - start), counter.total())
}

func runBaselineRound() async -> (Double, Int) {
    var counts: [String: Int] = [:]          // 无同步单任务：工作量对照基线
    let clock = ContinuousClock()
    let start = clock.now
    for w in 0..<workers {
        for _ in 0..<perWorker { counts["w\(w)", default: 0] += 1 }
    }
    return (ms(clock.now - start), counts.values.reduce(0, +))
}

// ---- hop 放大效应：逐次 await vs 攒一批一次提交 ----
func runFineGrained() async -> Double {
    let actor = CounterActor()
    let clock = ContinuousClock()
    let start = clock.now
    for _ in 0..<expectedTotal { await actor.bump("hot") }      // 20000 次 hop
    _ = await actor.total()
    return ms(clock.now - start)
}

func runBatched() async -> Double {
    let actor = CounterActor()
    let clock = ContinuousClock()
    let start = clock.now
    await actor.bumpBatch("hot", times: expectedTotal)          // 1 次 hop
    _ = await actor.total()
    return ms(clock.now - start)
}

print("=== 三实现基准（\(workers) 并发 × \(perWorker) 次，每轮应得 \(expectedTotal)）===")
for round in 1...rounds {
    let (tActor, cActor) = await runActorRound()
    let (tLock, cLock) = await runLockRound()
    let (tBase, cBase) = await runBaselineRound()
    let warm = round == 1 ? "（预热轮）" : ""
    print(String(format: "第%d轮%@：actor %.2fms(计数%d) | NSLock %.2fms(计数%d) | 无同步基线 %.2fms(计数%d)",
                 round, warm, tActor, cActor, tLock, cLock, tBase, cBase))
    assert(cActor == expectedTotal && cLock == expectedTotal && cBase == expectedTotal, "计数必须精确")
}

print("\n=== hop 放大效应：同等 20000 次写入 ===")
// 先各预热一遍，再量两轮取较小值，排掉首轮预热
for warmup in 0...1 {
    let fine = await runFineGrained()
    let batch = await runBatched()
    if warmup == 1 {
        print(String(format: "逐次 await（20000 次 hop）：%.2fms", fine))
        print(String(format: "批量一次（1 次 hop）：%.2fms", batch))
        print(String(format: "放大倍数：%.0fx —— 工作量一样，差的只是 hop 次数", fine / batch))
    }
}

print("""

结论（对应 M4/C5）：
- 三实现计数全精确（20000）——同步正确性不是问题，问题在成本。
- hop 放大效应比预期猛：同样 20000 次写入，逐次 await 与批量一次差出数千倍——
  批量化不是微优化，是数量级决策。C5 那句「单次 hop 不可怕，可怕的是 N×hop」拿到实锤。
- 诚实声明（度量完整性）：本实验跑在 swift CLI 解释器里，每次 await/锁调用都被
  解释开销放大，绝对耗时（十几秒干 20000 次增量）不代表编译产物；actor vs NSLock
  的相对差距（本环境 ~1.3x）也不能直接推广——这条对照记「待真机验证」。
  M1 的纪律反咬一口：测量工具本身会污染数据，基准结论必须连同测量环境一起声明。
- 优先级反转未在本实验覆盖（记观察项）。
""")
