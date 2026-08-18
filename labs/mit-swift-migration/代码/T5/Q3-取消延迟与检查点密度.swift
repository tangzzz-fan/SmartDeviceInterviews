// T5-Q3 取消延迟与检查点密度实验（载体 3.2 延伸，T3 遗留 3 + T2 遗留 1 回收）
// 思路：长循环任务，三组检查点密度：①每次迭代查 Task.isCancelled；②每 10_000 次批检；
// ③不检查（对照组，cancel 后照跑到自然结束——「停不下来」本身就是证据）。
// 两组测量：a) 无取消全程跑完 → 循环总耗时（检查点开销的账）；
//          b) 任务跑到 50% 进度时发起 cancel → 「cancel → 实际退出」的延迟。
// 撞墙记录①：初版 iterations = 5_000_000，在 swift CLI 解释器里单组循环要跑 9 分钟，
// 三组全量跑完近半小时——实验设计没考虑「测量环境也是成本」。设计基准先估算环境速度，
// 结论只认相对关系，绝对值随环境漂移（与 Q2 同一课）。
// 撞墙记录②：初版取消时机是「启动后 sleep 0.1s 再 cancel」——小迭代量下三组延迟全是 ~1.7ms，
// 数据假得离谱。复盘：sleep 只保证「过了 0.1s」，不保证 worker 已经在跑——解释器里
// worker 可能还没被调度、或已在 0.1s 内跑完，量到的是调度噪声不是取消行为。
// 修正：worker 跑到 50% 进度（信号量打点）才发起 cancel——取消时任务确实在循环里，
// 延迟才有意义。教训：测取消先保证「被取消者已就位」，否则量的是调度不是取消。
// .task 修饰符的寿命绑定（T2 遗留 1）：CLI 无视图，口述勾连，不冒充实测。
import Foundation

let iterations = 500_000
let checkpoint = iterations / 2        // 跑到一半时发起取消

func ms(_ d: Duration) -> Double { Double(d.components.seconds) * 1000 + Double(d.components.attoseconds) / 1e12 }

// ---- 循环体：轻量累加。checkEvery == nil 表示不检查（对照组）----
// onProgress：跨过 50% 进度时通知一次（给测量方一个「我已就位」的信号）
func runLoop(checkEvery: Int?, onProgress: @Sendable @escaping () -> Void) async -> Int {
    var sum = 0
    var announced = false
    for i in 0..<iterations {
        if !announced && i >= checkpoint { announced = true; onProgress() }
        if let every = checkEvery, i % every == 0, Task.isCancelled { return sum }
        sum &+= i &* 3 &+ 1
    }
    return sum
}

// ---- 测量一：无取消全程跑完（循环总耗时 = 检查点开销的账）----
func measureFullLoop(checkEvery: Int?) async -> Double {
    let clock = ContinuousClock()
    let start = clock.now
    _ = await runLoop(checkEvery: checkEvery, onProgress: {})
    return ms(clock.now - start)
}

// ---- 测量二：worker 就位（跑到 50%）后 cancel，量「cancel → 实际退出」延迟 ----
func measureCancelLatency(checkEvery: Int?) async -> Double {
    let clock = ContinuousClock()
    let reached = DispatchSemaphore(value: 0)
    let task = Task.detached {
        await runLoop(checkEvery: checkEvery, onProgress: { reached.signal() })
    }
    reached.wait()                              // 确保 worker 确实在循环里，才开始计时
    let cancelAt = clock.now
    task.cancel()
    _ = await task.value
    return ms(clock.now - cancelAt)
}

print("=== 检查点密度对照（\(iterations) 次迭代，任务跑到 50% 时发起取消）===")
print("组\t循环总耗时(无取消)\t取消延迟")

let groups: [(String, Int?)] = [("①每次检查", 1), ("②每1万次批检", 10_000), ("③不检查", nil)]
for (name, every) in groups {
    let full = await measureFullLoop(checkEvery: every)
    let latency = await measureCancelLatency(checkEvery: every)
    print(String(format: "%@\t%.0fms\t%.1fms", name, full, latency))
}

print("""

结论（对应 M4/C3）：
- 取消不杀代码：③组收到 cancel 也照跑不误，取消延迟 ≈ 剩余半程的循环时间——
  「cancel 了就立刻停」在新世界不成立，停不停取决于循环体配不配合。
- 检查点有开销：①组每圈查一次，全程耗时高于③组——响应性的代价是吞吐。
- 密度原则有数据撑腰了：批检的取消延迟 ≈ 单批跑完所需时间（与批大小成正比），
  循环体轻、容忍秒级内停 → 批检（开销近零）；要求立即停或单圈代价大 → 每圈检查。
  不是越密越好，是「按停止时延预算选密度」。
- .task 修饰符勾连（T2 遗留 1，口述不冒充实测）：视图消失即自动 cancel，
  等于框架替你答了「这个任务该活多久」——和手动 Task「自己答取消时机」（T4 C1 同款义务）
  相对照。CLI 里没有视图，这条记口述验证。
""")
