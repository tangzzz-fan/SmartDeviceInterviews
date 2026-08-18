// T3-Q3 actor 缓存的可重入翻车现场（挂载体 3.3 前置）
// 思路：actor 不是串行队列——挂起点会「松手」。check-then-act 跨挂起点会被重入打穿。
// 撞墙记录：第一版我断言 fetchCount == 1（以为 actor 像串行队列一样堵门，
// 一个请求没完第二个进不来），实跑却是 2——第二个请求在挂起窗口里进来读到了空缓存。
// 串行队列经验在这里是负资产：堵门 vs 让位，一字之差。
import Foundation

var fetchCount = 0 // 全局计数器当证据（T1-Q2 教训：计数器放全局，不放类型里）

@MainActor
func fakeFetch(_ key: String) async -> Data {
    fetchCount += 1
    let n = fetchCount
    print("  [fetch] \(key) #\(n) 发起")
    try? await Task.sleep(nanoseconds: 300_000_000) // 模拟网络 IO
    return Data(key.utf8)
}

// 版本 1：check-then-act——await 之前检查过了，挂起之后世界已经变了
actor ImageCacheV1 {
    private var cache: [String: Data] = [:]
    func image(for key: String) async -> Data {
        if let hit = cache[key] {
            print("  [V1] \(key) 命中缓存")
            return hit
        }
        let data = await fakeFetch(key) // ← 挂起点：actor 松手，另一个调用者进来
        cache[key] = data
        return data
    }
}

// 版本 2：把「挂起期间的承诺」也存进状态——in-flight 去重
actor ImageCacheV2 {
    private var cache: [String: Data] = [:]
    private var inFlight: [String: Task<Data, Never>] = [:]

    func image(for key: String) async -> Data {
        if let hit = cache[key] {
            print("  [V2] \(key) 命中缓存")
            return hit
        }
        if let ongoing = inFlight[key] {
            print("  [V2] \(key) 复用 in-flight 任务，不重复 fetch")
            return await ongoing.value
        }
        let task = Task { await fakeFetch(key) }
        inFlight[key] = task // 先登记承诺，再挂起等待
        let data = await task.value
        inFlight[key] = nil
        cache[key] = data
        return data
    }
}

print("=== 版本 1：两个并发请求同一 key ===")
let v1 = ImageCacheV1()
async let r1 = v1.image(for: "avatar")
async let r2 = v1.image(for: "avatar")
_ = await (r1, r2)
print("证据：fetchCount =", fetchCount, "（预期 2：重入打穿了 check-then-act）")
assert(fetchCount == 2, "版本 1 必须重复 fetch——这就是翻车现场的活体标本")

print("=== 版本 2：in-flight 去重 ===")
let before = fetchCount
let v2 = ImageCacheV2()
async let s1 = v2.image(for: "avatar")
async let s2 = v2.image(for: "avatar")
_ = await (s1, s2)
print("证据：本轮 fetch 次数 =", fetchCount - before, "（预期 1：第二个复用 in-flight 任务）")
assert(fetchCount - before == 1, "版本 2 必须只 fetch 一次")
print("Q3 验证通过：actor 在挂起点让位；check-then-act 要把承诺也存进状态")
