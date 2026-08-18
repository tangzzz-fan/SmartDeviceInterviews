// T5-Q4 Actor 化重构：共享可变缓存 + 可重入现场
import Foundation

actor Cache {
    private var store: [String: String] = [:]
    func get(_ k: String) -> String? { store[k] }
    func set(_ k: String, _ v: String) { store[k] = v }
    // 可重入现场：挂起期间状态被别人改
    func checkThenAct(key: String, delay: UInt64) async -> String? {
        guard let current = store[key] else { return nil }
        try? await Task.sleep(nanoseconds: delay)   // 挂起，让出执行权
        return store[key]                           // 挂起前后状态可能已变
    }
}

let sem = DispatchSemaphore(value: 0)
Task {
    let cache = Cache()
    await cache.set("k", "v1")
    async let a = cache.checkThenAct(key: "k", delay: 200_000_000)
    try? await Task.sleep(nanoseconds: 50_000_000)
    await cache.set("k", "v2")   // 挂起期间被改
    let r = await a
    print("可重入现场: 读到的初始值 v1，挂起后 store 里是 v2，checkThenAct 返回 \(r ?? "nil")（check-then-act 失效）")
    print("actor 语义: 串行执行 + 可重入 + 隔离域；与锁的差异=挂起时让位而非死等")
    sem.signal()
}
sem.wait()
