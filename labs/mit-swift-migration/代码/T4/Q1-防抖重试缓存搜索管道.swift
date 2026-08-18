// T4-Q1 防抖+重试+缓存搜索管道（挂载体 4.2 本体）
// 思路：PassthroughSubject 收抖动输入 → debounce 只留最后一次 → removeDuplicates
// → flatMap 请求（首次失败模拟）→ retry(1) → catch 兜底；每阶段打时间戳。
// 我的疑点：缓存字典该挂 debounce 前还是后——先放 flatMap 里查，命中直接返回不发请求。
// 撞墙记录①：第一版我直接在 flatMap 里 return 缓存的 Just，编译不过——
// Just<[String], Never> 和 fakeSearch 的 AnyPublisher<[String], Error> Failure 对不上，
// 管道的错误类型全程必须一致。用 Just(...).setFailureType(to: Error.self) 抹平才过。
// 这才实感 M3 那句「Failure 是类型参数、沿管道全程流转」——错误类型也是管道形状的一部分。
// 撞墙记录②：catch 兜底第一版写 Just<[String], Error>([])——Just 只有一个泛型参数，
// Failure 恒为 Never，编译器当场拒绝；同样要 setFailureType 抬类型。同一天撞两次同款墙，记深了。
// 撞墙记录③：第二轮本想重发同 key 验缓存，但同 key 连着发会被 removeDuplicates 挡掉——
// 「缓存命中不涨计数」会被去重冒充。改成先发新 key（swiftui）再回头发 swift，
// 既保住去重管道、又让缓存命中拿到真证据。
import Foundation
import Combine

func ts() -> String { String(format: "%.2fs", CFAbsoluteTimeGetCurrent() - start) }
let start = CFAbsoluteTimeGetCurrent()

// ---- 假网络：同 key 首次失败，用计数打点证明 retry 是「重新订阅」----
var requestCounts: [String: Int] = [:]
func fakeSearch(_ q: String) -> AnyPublisher<[String], Error> {
    Deferred {
        Future<[String], Error> { promise in
            requestCounts[q, default: 0] += 1
            let n = requestCounts[q]!
            print("    [\(ts())] 请求发出 #\(n)（key=\(q)）")
            if n == 1 {
                promise(.failure(NSError(domain: "net", code: -1)))
            } else {
                promise(.success([q + "-resultA", q + "-resultB"]))
            }
        }
    }
    .eraseToAnyPublisher()
}

// ---- 缓存：命中直接回值，不发请求 ----
var cache: [String: [String]] = [:]
func searchWithCache(_ q: String) -> AnyPublisher<[String], Error> {
    if let hit = cache[q] {
        print("    [\(ts())] 缓存命中（key=\(q)），不发请求")
        return Just(hit).setFailureType(to: Error.self).eraseToAnyPublisher()
    }
    return fakeSearch(q)
        .handleEvents(receiveOutput: { cache[q] = $0 })
        .eraseToAnyPublisher()
}

let input = PassthroughSubject<String, Never>()
var bag = Set<AnyCancellable>()

input
    .handleEvents(receiveOutput: { print("[\(ts())] 击键：\($0)") })
    .debounce(for: .milliseconds(300), scheduler: RunLoop.main)
    .handleEvents(receiveOutput: { print("[\(ts())] debounce 放行：\($0)") })
    .removeDuplicates()
    .flatMap { q in
        searchWithCache(q)
            .retry(1)                                    // 失败时重新订阅上游（计数打点验证）
            .catch { _ in Just<[String]>([]).setFailureType(to: Error.self) }    // 兜底：重试仍败就吐空结果，管道不死
    }
    .sink(
        receiveCompletion: { print("[\(ts())] 管道完成：\($0)") },
        receiveValue: { print("[\(ts())] ✅ 结果：\($0)") }
    )
    .store(in: &bag)

// ---- 第一轮：抖动输入 s/sw/swi/swift，debounce 应只放行 swift ----
for s in ["s", "sw", "swi"] { input.send(s); Thread.sleep(forTimeInterval: 0.05) }
Thread.sleep(forTimeInterval: 0.4)   // 静默 > 0.3s，debounce 放行 swi
input.send("swift")
// 跑主 RunLoop 驱动 debounce 定时器与 Future
let deadline = Date().addingTimeInterval(1.0)
while Date() < deadline { RunLoop.main.run(mode: .default, before: deadline) }

// ---- 第二轮：先发新 key（miss），再回头发 swift 验缓存命中（请求计数不涨）----
input.send("swiftui")
let deadline2 = Date().addingTimeInterval(0.6)
while Date() < deadline2 { RunLoop.main.run(mode: .default, before: deadline2) }
input.send("swift")   // 与上一个 swiftui 不重复，能穿过去重 → 命中缓存
let deadline3 = Date().addingTimeInterval(0.6)
while Date() < deadline3 { RunLoop.main.run(mode: .default, before: deadline3) }

print("请求计数：\(requestCounts)（swift=2：首败+retry 成；swiftui=2 同款；缓存轮回不涨）")
assert(requestCounts["swift"] == 2, "swift 缓存命中后不该再发请求")
assert(requestCounts["swiftui"] == 2, "swiftui 首败 + retry 应各一次")
print("断言通过：debounce 只留最后输入 / retry=重新订阅 / 缓存命中不涨计数 / catch 兜底管道不死")
