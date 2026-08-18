// T6 Q1：存量管道迁移与对拍（Combine 版 vs async 手写版）
// 环境：Apple Swift 6.3.3（swift-driver 1.148.6, arm64-apple-macosx26.0），顶层脚本 `swift Q1-存量管道迁移与对拍.swift` 实跑。
// 任务：复刻搜索管道（文本流 → debounce → 去重 → 模拟请求(retry 2) → 收集），
//       Combine 版与 async 迁移版喂相同输入序列，对拍输出一致才算迁完。
// 环境约束：CLI 不可用 AsyncAlgorithms（外部 SPM 包），debounce/retry 手写——手写即拷问点。
//
// 撞墙记录（如实留档）：
// ① 手写 debounce 第一版用「单次超时即判静默期满」，10ms 静默就发（窗口 80ms 名存实亡）；
//    改「静默累计/时间戳比较」（新值续期清零，对齐 Combine 的 due: 每次新值重置静默计时）。
// ② 手写 retry 第一版最后一次失败只 break 不 throw，失败被吞成「静默成功」——对拍时
//    Combine 版抛错、async 版空结果，才暴露。教训：手写算子先写失败路径。
// ③ Combine 版 receive(on: DispatchQueue.main) 在 CLI 顶层脚本取不到事件（RunLoop 不转，
//    T4 Q3/T5 Q4 同款墙的亲戚）——去掉 receive(on:)，在 sink 里用锁归集结果；
//    「回主线程」语义在 CLI 记口述等价，真机版保留 receive(on:)（待真机验证）。
// ④ 第二版想用「nextOrTimeout 竞速拉取」，撞两堆墙：扩展方法与 AsyncSequence.next() 同名遮蔽；
//    超时侧胜出时取消挂起的 iterator.next() 会终止整条 AsyncStream（取消即终止语义）。
//    终版改「推模型」：reader 任务消费源流写共享状态，emitter 任务按 10ms 时钟轮询静默期——
//    手写算子选结构比选语法更要命：拉模型竞速碰取消，就用推模型+时钟。

import Combine
import Foundation

// MARK: - 共享输入与请求模拟（两版对拍的同一份原料）

// burst 语义：前三个输入间隔远小于 debounce 窗口 → 收敛成最新值；sleep 后的输入独立成事件
let inputBurst: [(text: String, delayMs: Int)] = [
    ("s", 0), ("sw", 10), ("swi", 10),   // burst → 收敛为 "swi"
    ("swift", 200),                        // 静默后独立事件
]

final class FakeAPI: @unchecked Sendable {
    private let lock = NSLock()
    private var attemptsByQuery: [String: Int] = [:]
    // 每个 query 前两次失败、第三次成功——两版共用，保证 retry 行为同口径
    func fetch(_ query: String) throws -> String {
        lock.lock(); defer { lock.unlock() }
        attemptsByQuery[query, default: 0] += 1
        let n = attemptsByQuery[query]!
        if n <= 2 { throw URLError(.networkConnectionLost) }
        return "结果(\(query))"
    }
}

// MARK: - 旧世界：Combine 版管道

func runCombinePipeline(api: FakeAPI) -> [String] {
    let subject = PassthroughSubject<String, Never>()
    var results: [String] = []
    let resultLock = NSLock()
    let done = DispatchSemaphore(value: 0)

    let cancellable = subject
        .debounce(for: .milliseconds(80), scheduler: DispatchQueue.global())
        .removeDuplicates()
        .map { query -> String in
            // 手写 retry 2（Combine 的 .retry(2) 语义：初次 + 2 次重试 = 共 3 次）
            var lastError: Error?
            for _ in 0..<3 {
                do { return try api.fetch(query) } catch { lastError = error }
            }
            Swift.print("  [Combine] query=\(query) 三次全失败：\(lastError!)")
            return ""   // 本例输入保证第三次成功，此分支为对称性保留
        }
        .sink { value in
            resultLock.lock(); results.append(value); resultLock.unlock()
            done.signal()
        }
    _ = cancellable   // 凭证存住（T4 C1 的义务），函数返回前不取消

    // 按节拍喂输入（生产侧带节拍）
    for item in inputBurst {
        if item.delayMs > 0 { Thread.sleep(forTimeInterval: Double(item.delayMs) / 1000) }
        subject.send(item.text)
    }
    done.wait(); done.wait()   // 等两个输出事件
    subject.send(completion: .finished)
    resultLock.lock(); defer { resultLock.unlock() }
    return results
}

// MARK: - 新世界：async 手写版管道

// 共享状态：reader 写、emitter 读（锁担保，@unchecked 纪律：单读者单写者已在结构上保证）
final class DebounceState: @unchecked Sendable {
    private let lock = NSLock()
    private var latest: String?
    private var lastUpdate = Date()
    private var finished = false
    func update(_ value: String) {
        lock.lock(); latest = value; lastUpdate = Date(); lock.unlock()   // 新值续期：重置静默计时
    }
    func markFinished() { lock.lock(); finished = true; lock.unlock() }
    func takeIfSilent(_ ms: Int) -> String? {
        lock.lock(); defer { lock.unlock() }
        guard let value = latest, Date().timeIntervalSince(lastUpdate) * 1000 >= Double(ms) else { return nil }
        latest = nil
        return value
    }
    func drainedAndFinished() -> Bool {
        lock.lock(); defer { lock.unlock() }
        return finished && latest == nil
    }
}

// 手写 debounce：推模型——reader 消费源流写状态，emitter 按 10ms 时钟轮询静默期（撞墙④终版）
func debounce(intervalMs: Int, source: AsyncStream<String>) -> AsyncStream<String> {
    AsyncStream { continuation in
        let state = DebounceState()
        let reader = Task {
            for await value in source { state.update(value) }
            state.markFinished()    // 上游结束：尾值由 emitter 冲刷
        }
        let emitter = Task {
            while !Task.isCancelled {
                try? await Task.sleep(for: .milliseconds(10))
                if let value = state.takeIfSilent(intervalMs) { continuation.yield(value) }
                if state.drainedAndFinished() { break }
            }
            continuation.finish()
        }
        continuation.onTermination = { _ in reader.cancel(); emitter.cancel() }
    }
}

// 手写 retry：n 次尝试，最后一次仍失败要抛（撞墙②的教训）
func withRetry<T>(_ attempts: Int, _ body: () throws -> T) throws -> T {
    var lastError: Error?
    for attempt in 1...attempts {
        do { return try body() }
        catch {
            lastError = error
            if attempt == attempts { throw error }
        }
    }
    throw lastError!
}

func runAsyncPipeline(api: FakeAPI) async -> [String] {
    // 生产侧：同一份输入节拍（对齐 Combine 版）
    let source = AsyncStream<String> { continuation in
        Task {
            for item in inputBurst {
                if item.delayMs > 0 { try? await Task.sleep(for: .milliseconds(item.delayMs)) }
                continuation.yield(item.text)
            }
            continuation.finish()
        }
    }
    var results: [String] = []
    var last: String?
    for await query in debounce(intervalMs: 80, source: source) {
        // 手写去重（removeDuplicates 等价）
        if query == last { continue }
        last = query
        let result = try! withRetry(3) { try api.fetch(query) }
        results.append(result)
    }
    return results
}

// MARK: - 对拍

let apiCombine = FakeAPI()
let apiAsync = FakeAPI()

Swift.print("=== Combine 版管道 ===")
let combineResults = runCombinePipeline(api: apiCombine)
Swift.print("输出序列：\(combineResults)")

Swift.print("\n=== async 手写版管道 ===")
let asyncResults = await runAsyncPipeline(api: apiAsync)
Swift.print("输出序列：\(asyncResults)")

Swift.print("\n=== 对拍 ===")
Swift.print("Combine 版：\(combineResults)")
Swift.print("async   版：\(asyncResults)")
if combineResults == asyncResults {
    Swift.print("✅ 对拍一致——迁移完成（同输入序列、同输出序列、retry 均 3 次尝试后成功）")
} else {
    Swift.print("❌ 对拍不一致——迁移未完成，查 debounce 语义差（窗口起算点/续期）")
}
Swift.print("\n语义差异笔记：Combine .debounce 在指定 scheduler 上按「最后一次收到值 + 窗口」到期发出；")
Swift.print("手写版 latest+静默检查是同一语义的轮询实现（检查粒度 10ms ≪ 窗口 80ms），真机/真包用 AsyncAlgorithms.debounce 替代。")
