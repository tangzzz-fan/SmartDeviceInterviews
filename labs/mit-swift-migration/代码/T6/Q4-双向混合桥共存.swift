// T6 Q4：双向混合桥共存——values（旧→新）与 AsyncPublisher（新→旧）同场对拍
// 环境：Apple Swift 6.3.3（swift-driver 1.148.6, arm64-apple-macosx26.0），顶层脚本实跑。
// 任务：桥 A（旧→新）：Combine 侧 PassthroughSubject 供货，async 侧 for await subject.values 消费；
//       桥 B（新→旧）：async 侧 AsyncStream 供货，Combine 侧 AsyncPublisher(...).sink 消费。
//       两桥各自对拍「生产 N = 消费 N」，时序防线：先挂消费者再开生产者（T5 Q4 教训），0 丢件。
//       寿命差异：values 的迭代归消费循环（Task 取消即终止），AsyncPublisher 的订阅归 cancellable（回到旧世界义务）。
//
// 撞墙记录（如实留档）：
// ① 时序防线没有握手信号可挂——CLI 里拿不到「values 已订阅就位」的回调，
//    只能用节拍（消费任务启动后 sleep 50ms 再开生产者）。防线靠节拍不靠回调，如实声明；
//    真机版可换 CurrentValueSubject 带初始状态或异步 gate 做确定性握手。
// ② 两条桥对「先发后挂」的容忍度不对称（对拍时故意各做一次反例对照）：
//    桥 A（热 subject + values）先 send 后订阅 = 丢件（T5 Q4 段二同款翻车，热源没有缓冲）；
//    桥 B（AsyncStream + 手搭桥）先发后 sink = 不丢（AsyncStream 默认 unbounded 缓冲，
//    冷启动语义替你把早到的件存住）——丢件归责先查「桥有没有缓冲」，再查「谁先就位」。
// ③ 桥 B 第一版写 `AsyncPublisher(stream).sink` 编译不过——撞出真墙：Combine 的 AsyncPublisher
//    是 Publisher→AsyncSequence 方向的桥（和 .values 同向），不是反向桥；标准库没有现成的
//    AsyncStream→Publisher 桥。正解：手搭——Task 泵流 + PassthroughSubject 转发，
//    泵 Task 的寿命交给消费侧 cancellable 管（onTermination/手动 cancel）。
//    教训：「新→旧」桥没有白嫌的现成件，手搭桥本身就是 M2 账本里「缺项自建」的一行。

import Combine
import Foundation

// MARK: - 共享工具

final class LockedArray: @unchecked Sendable {
    private let lock = NSLock()
    private var items: [Int] = []
    func append(_ v: Int) { lock.lock(); items.append(v); lock.unlock() }
    var snapshot: [Int] { lock.lock(); defer { lock.unlock() }; return items }
}

// subject 薄壳：PassthroughSubject 不 Sendable，锁内 send 担保跨隔离域安全（Q3 同款）
final class IntBus: @unchecked Sendable {
    let subject = PassthroughSubject<Int, Never>()
    func send(_ i: Int) { lock.lock(); subject.send(i); lock.unlock() }
    func finish() { lock.lock(); subject.send(completion: .finished); lock.unlock() }
    private let lock = NSLock()
}

// 流桥：continuation 建流时接入，生产者按节拍供货（Q3 同款）
final class StreamBridge: @unchecked Sendable {
    private let lock = NSLock()
    private var continuation: AsyncStream<Int>.Continuation?
    func wire(_ c: AsyncStream<Int>.Continuation) { lock.lock(); continuation = c; lock.unlock() }
    func yield(_ v: Int) { lock.lock(); continuation?.yield(v); lock.unlock() }
    func finish() { lock.lock(); continuation?.finish(); lock.unlock() }
}

let N = 6   // 每桥供货件数

// MARK: - 桥 A（旧→新）：PassthroughSubject → .values → for await

func runBridgeA() async -> (sent: Int, received: Int, items: [Int]) {
    let bus = IntBus()
    let receivedItems = LockedArray()

    // 时序防线（撞墙①）：先挂消费者——消费任务就位、values 订阅生效后再开生产者
    let consumer = Task.detached {
        for await value in bus.subject.values {
            receivedItems.append(value)
        }
    }
    try? await Task.sleep(for: .milliseconds(50))   // 节拍等订阅就位（CLI 无握手回调，如实声明）

    // 开生产者：N 件带节拍 + completion 收尾（values 迭代随 finished 结束）
    let producer = Task.detached {
        for i in 1...N {
            bus.send(i)
            try? await Task.sleep(for: .milliseconds(10))
        }
        bus.finish()
    }
    await producer.value
    await consumer.value        // 消费循环的寿命：for-await 随 finished 退出——迭代归消费侧
    return (N, receivedItems.snapshot.count, receivedItems.snapshot)
}

// MARK: - 桥 B（新→旧）：AsyncStream → 手搭桥（Task 泵流 + subject 转发）→ sink

// 手搭新→旧桥（撞墙③）：AsyncPublisher 是反方向的桥，AsyncStream→Publisher 没有现成件；
// Task 泵流把件倒进 subject，sink 照常订阅——泵 Task 就是桥上的「旧世界义务」：要人管取消
final class AsyncToCombineBridge: @unchecked Sendable {
    let subject = PassthroughSubject<Int, Never>()
    private var pump: Task<Void, Never>?
    func connect(_ stream: AsyncStream<Int>) {
        pump = Task.detached { [subject] in
            for await value in stream { subject.send(value) }
            subject.send(completion: .finished)     // 流结束 → 旧世界收到 finished
        }
    }
    func disconnect() {
        pump?.cancel()
        pump = nil
    }
}

func runBridgeB() async -> (sent: Int, received: Int, items: [Int]) {
    let bridge = StreamBridge()
    let stream = AsyncStream<Int> { continuation in bridge.wire(continuation) }
    let receivedItems = LockedArray()

    // 手搭新→旧桥（撞墙③）
    let toCombine = AsyncToCombineBridge()

    // 时序防线（撞墙①）：先挂消费者——sink 就位（cancellable 在手）再接流、再开生产者
    var bag = Set<AnyCancellable>()
    toCombine.subject
        .sink { value in receivedItems.append(value) }
        .store(in: &bag)        // 旧世界义务回归：订阅凭证要人存（T4 C1 的账在桥上没免）
    toCombine.connect(stream)   // 泵 Task 启动（寿命归桥，手动 disconnect 或随 finished 自了）

    let producer = Task.detached {
        for i in 1...N {
            bridge.yield(i)
            try? await Task.sleep(for: .milliseconds(10))
        }
        bridge.finish()         // 流结束 → 泵转发 finished → sink 完成
    }
    await producer.value
    // sink 的投递在泵任务里异步落地，轮询等账齐（1s 超时兜底）
    for _ in 0..<100 {
        if receivedItems.snapshot.count == N { break }
        try? await Task.sleep(for: .milliseconds(10))
    }
    toCombine.disconnect()      // 桥的寿命了结：泵 Task 手动取消（旧世界义务不免费）
    bag.removeAll()             // cancellable 寿命了结：凭证随作用域退出
    return (N, receivedItems.snapshot.count, receivedItems.snapshot)
}

// MARK: - 反例对照（撞墙②）：先发后挂，两桥的丢件容忍度不对称

func runAntiPatterns() async -> (aReceived: Int, bLost: Int) {
    // 桥 A 反例：热 subject 先 send 后订阅——丢件
    let bus = IntBus()
    for i in 1...3 { bus.send(i) }                  // 无人订阅的 send：热源的件落地即丢
    let receivedA = LockedArray()
    let consumer = Task.detached {
        for await v in bus.subject.values { receivedA.append(v) }
    }
    try? await Task.sleep(for: .milliseconds(30))
    bus.send(4)                                     // 订阅后的件才收得到
    bus.finish()
    await consumer.value

    // 桥 B 反例：AsyncStream 先 yield 后接桥/sink——不丢（unbounded 缓冲存住早到的件）
    let bridge = StreamBridge()
    let stream = AsyncStream<Int> { c in bridge.wire(c) }
    for i in 1...3 { bridge.yield(i) }              // 尚无消费者：缓冲存住
    let receivedB = LockedArray()
    let toCombineB = AsyncToCombineBridge()
    var bag = Set<AnyCancellable>()
    toCombineB.subject
        .sink { receivedB.append($0) }
        .store(in: &bag)
    toCombineB.connect(stream)                      // 接桥：缓冲里的 3 件被泵出来
    for _ in 0..<100 {
        if receivedB.snapshot.count == 3 { break }
        try? await Task.sleep(for: .milliseconds(10))
    }
    bridge.finish()
    for _ in 0..<50 { try? await Task.sleep(for: .milliseconds(2)) }   // 等 finished 落地
    toCombineB.disconnect()
    bag.removeAll()
    return (receivedA.snapshot.count, 3 - receivedB.snapshot.count)
}

// MARK: - 对拍驱动

Swift.print("=== 桥 A（旧→新）：PassthroughSubject → .values → for await ===")
let a = await runBridgeA()
Swift.print("生产 \(a.sent) 件 / 消费 \(a.received) 件，序列：\(a.items)")
Swift.print(a.sent == a.received ? "✅ 桥 A 0 丢件" : "❌ 桥 A 丢件：差 \(a.sent - a.received)")

Swift.print("\n=== 桥 B（新→旧）：AsyncStream → 手搭桥（Task 泵流 + subject 转发）→ sink ===")
let b = await runBridgeB()
Swift.print("生产 \(b.sent) 件 / 消费 \(b.received) 件，序列：\(b.items)")
Swift.print(b.sent == b.received ? "✅ 桥 B 0 丢件" : "❌ 桥 B 丢件：差 \(b.sent - b.received)")

Swift.print("\n=== 反例对照（撞墙②）：先发后挂，两桥容忍度不对称 ===")
let anti = await runAntiPatterns()
Swift.print("桥 A（热 subject）先发 3 件后订阅：只收到 \(anti.aReceived) 件（订阅后的第 4 件）——热源无缓冲，前 3 件落地即丢")
Swift.print("桥 B（AsyncStream）先发 3 件后 sink：丢 \(anti.bLost) 件——unbounded 缓冲把早到的件存住")
Swift.print(anti.aReceived == 1 && anti.bLost == 0 ? "✅ 缓冲不对称实锤：丢件归责先查桥有没有缓冲、再查谁先就位" : "❌ 缓冲语义与预期不符（A 应收 1、B 应丢 0）")

Swift.print("\n=== 寿命管理差异（两桥共存时的义务归属）===")
Swift.print("桥 A（values）：迭代寿命归消费循环——Task 取消/for-await 退出即终止，结构化担保；")
Swift.print("桥 B（手搭桥）：订阅寿命归 cancellable + 泵 Task 归 disconnect——回到旧世界「记得存、记得取消」的义务（T4 C1）；")
Swift.print("混合期两桥共存 = 两套寿命制度并行：新侧靠结构、旧侧靠纪律，桥是边界不是过渡品（M5/D1）。")
Swift.print("补记（撞墙③）：AsyncPublisher 是 Publisher→AsyncSequence 方向的桥（与 .values 同向），反向桥无现成件，手搭即 M2 的「缺项自建」。")
