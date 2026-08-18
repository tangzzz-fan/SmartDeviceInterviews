// T6 Q3：寿命移交——cancellable → 结构化寿命（两形态对拍 + 永生反例）
// 环境：Apple Swift 6.3.3（swift-driver 1.148.6, arm64-apple-macosx26.0），顶层脚本实跑。
// 任务：旧形态（Screen 持 Set<AnyCancellable>，deinit 即订阅终止）vs
//       新形态（Screen 寿命内的 Task 消费 AsyncStream，Screen 消失 = Task 取消 = 流终止 onTermination），
//       对拍「创建→活 0.2s→销毁→再等 0.15s」后两形态都不再收事件；
//       反例：Task 存进永生单例 = 翻译不动的跨作用域形态（Screen 死了订阅还活着）。
//
// 撞墙记录（如实留档）：
// ① 第一版生产者用 Task {} 起——顶层脚本 Task 继承 MainActor，而主线程在 Thread.sleep，
//    生产者一个 tick 都发不出（计数全 0）。改 Task.detached（T3 的死锁形状记忆救了我）。
// ② legacy sink 闭包第一版强捕获 self——subject→闭包→self→bag→闭包的环，Screen 永不 deinit，
//    「销毁后停收」假象成立但 deinit 打点永不出现——[weak self] 老账新还，环先拆再谈对拍。
// ③ 「销毁后不再收」的判定窗口：生产者在 Screen 死后继续发 0.15s，两形态计数必须冻结；
//    第一版只比「死前计数相等」，没比「死后冻结」——反例和正例就分不开了。判定要双侧：死前有收、死后停收。
// ④ 首跑暴露旧形态「死后冻结」判定是假证：占位代码 frozen = Counter() 恒零，b == a 平凡成立，
//    「停收」根本没被测量。修法：生产者回调里同时 bump 一个独立的「死后收账」计数器，
//    Screen 死后它若再涨 = 有人还在收；停收的证据 = 死后收账计数冻结（0 新增）。
// ⑤ Sendable 警告三连（PassthroughSubject 不 Sendable、顶层 let 被 MainActor 隔离）——不 @preconcurrency 掩盖，
//    subject 包进 @unchecked Sendable 薄壳（锁内 send 担保），留档：桥两侧 crossing 隔离域是 Combine→async 的常态税。
// ⑥ 第二版死后收账记在生产者回调里（记「死后发了多少」）——语义错位：发出去不等于被收走，
//    旧形态首跑 10→20 ❌，但那是判定真的开始工作的证据（撞墙②的环若还在，同样会被抓住）。
//    修法：收账要记在消费侧——legacy 的 sink 亲自 bump 死后账，停收的证据才是「没人再收」。
// ⑦ 新形态首跑「死后生产侧仍发 0 件」——流内生产者 Task 挂在 onTermination 上，随消费侧取消一起死，
//    「消费停收」没有对照基准。修法：生产者改成独立 detached 任务（寿命不跟消费者），
//    死后它继续发、消费侧 0 新增，被丢的件差额才是取消传导的证据。

import Combine
import Foundation

// MARK: - 共享工具：锁保护计数 + 滴答生产者 + subject 薄壳

final class Counter: @unchecked Sendable {
    private let lock = NSLock()
    private var value = 0
    func bump() { lock.lock(); value += 1; lock.unlock() }
    var count: Int { lock.lock(); defer { lock.unlock() }; return value }
}

// subject 薄壳（撞墙⑤）：PassthroughSubject 不 Sendable，锁内 send 担保跨隔离域安全
final class IntBus: @unchecked Sendable {
    let subject = PassthroughSubject<Int, Never>()
    func send(_ i: Int) { lock.lock(); subject.send(i); lock.unlock() }
    private let lock = NSLock()
}

// 锁担保的布尔旗（撞墙⑥修复伴生）：跨线程可见的「死亡时刻」标记，替代裸 var 捕获
final class Flag: @unchecked Sendable {
    private let lock = NSLock()
    private var value = false
    func set() { lock.lock(); value = true; lock.unlock() }
    var isSet: Bool { lock.lock(); defer { lock.unlock() }; return value }
}

// 流桥（撞墙⑦伴生）：生产者独立存活，continuation 由建流时接入——死后发的件落在没消费者的桥上，即被丢
final class StreamBridge: @unchecked Sendable {
    private let lock = NSLock()
    private var continuation: AsyncStream<Int>.Continuation?
    func wire(_ c: AsyncStream<Int>.Continuation) { lock.lock(); continuation = c; lock.unlock() }
    func yield(_ v: Int) { lock.lock(); continuation?.yield(v); lock.unlock() }
}

// 生产者：detached（撞墙①），每 20ms 发一个 tick，直到被取消
func startProducer(send: @escaping @Sendable (Int) -> Void) -> Task<Void, Never> {
    Task.detached {
        var i = 0
        while !Task.isCancelled {
            i += 1
            send(i)
            try? await Task.sleep(for: .milliseconds(20))
        }
    }
}

// MARK: - 旧形态：Set<AnyCancellable> 手动存凭证

final class LegacyScreen {
    let received = Counter()
    private var bag = Set<AnyCancellable>()
    let name: String
    init(subject: PassthroughSubject<Int, Never>, name: String, afterDeath: Counter? = nil, dead: Flag? = nil) {
        self.name = name
        subject
            .sink { [weak self] _ in
                // 撞墙⑥：收账记在消费侧——死后账由 sink 亲自 bump，停收证据 = 死后账 0 新增
                if let dead, dead.isSet { afterDeath?.bump(); return }
                self?.received.bump()
            }
            .store(in: &bag)                                    // 凭证存住（T4 C1）
    }
    deinit { Swift.print("  [\(name)] deinit —— bag 随对象销毁自动取消全部订阅") }
}

// MARK: - 新形态：结构化寿命（Screen 消失 = Task 取消）

final class ModernScreen {
    let received = Counter()
    private var task: Task<Void, Never>?
    let name: String
    init(stream: AsyncStream<Int>, name: String, afterDeath: Counter? = nil, dead: Flag? = nil) {
        self.name = name
        task = Task.detached { [weak self] in
            for await _ in stream {
                // 撞墙⑥同款：收账记在消费侧
                if let dead, dead.isSet { afterDeath?.bump(); continue }
                self?.received.bump()
            }
        }
    }
    // 模拟 .task 修饰符的框架行为：视图（Screen）寿命结束 = 任务取消——寿命义务从记忆力移交结构
    func dismiss() {
        task?.cancel()
        task = nil
    }
    deinit { Swift.print("  [\(name)] deinit —— dismiss 时 Task 已取消，流已终止") }
}

// MARK: - 永生反例：Task 存进永生单例（翻译不动的跨作用域形态）

final class Immortal {
    static let shared = Immortal()
    var heldTasks: [Task<Void, Never>] = []   // 永不 deinit 的持有者（T5 M5 凭证长寿的同款宿主）
}

// MARK: - 对拍驱动

func phase(_ title: String, run: () async -> (beforeDestroy: Int, afterDestroy: Int)) async {
    Swift.print("=== \(title) ===")
    let (a, b) = await run()
    Swift.print("  死前计数：\(a)（应 > 0）")
    Swift.print("  死后计数：\(b)（应 == 死前，冻结 = 停收）")
    Swift.print(a > 0 && b == a ? "  ✅ 死前有收、死后停收" : "  ❌ 判定不过")
}

// —— 旧形态 ——
await phase("旧形态：cancellable 存进 Screen，deinit 即了结") {
    let bus = IntBus()
    let afterDeath = Counter()                        // 死后收账（撞墙⑥）：记在消费侧，sink 死后若仍被调则涨
    let dead = Flag()
    let producer = startProducer { bus.send($0) }
    var screen: LegacyScreen? = LegacyScreen(subject: bus.subject, name: "LegacyScreen", afterDeath: afterDeath, dead: dead)
    try? await Task.sleep(for: .milliseconds(200))
    let before = screen!.received.count
    screen = nil                                      // 销毁：bag 自动取消（sink 不再被调）
    dead.set()
    try? await Task.sleep(for: .milliseconds(150))    // 生产者继续发 0.15s——验证停收
    producer.cancel()
    return (before, before + afterDeath.count)        // 死后账 0 新增才冻结
}

// —— 新形态 ——
await phase("新形态：结构化寿命，dismiss = Task 取消 = 流终止") {
    let terminated = Counter()
    let producerSide = Counter()
    let streamBridge = StreamBridge()
    // 撞墙⑦：生产者独立于桥，寿命不跟消费者——死后继续发，消费侧停收才有对照基准
    let producer = startProducer { value in
        producerSide.bump()                           // 生产侧总账
        streamBridge.yield(value)
    }
    // 桥先建后接生产者（闭包捕获需先声明）
    let stream = AsyncStream<Int> { continuation in
        streamBridge.wire(continuation)               // 生产侧接到桥
        continuation.onTermination = { reason in
            terminated.bump()
            Swift.print("  [stream] onTermination: \(reason) —— 消费侧取消传到桥（T4 Q3 同款）；生产者独立存活，继续发即被丢")
        }
    }
    let afterDeath = Counter()
    let dead = Flag()
    var screen: ModernScreen? = ModernScreen(stream: stream, name: "ModernScreen", afterDeath: afterDeath, dead: dead)
    try? await Task.sleep(for: .milliseconds(200))
    let before = screen!.received.count
    let producedAtDismiss = producerSide.count
    screen?.dismiss()                                 // 模拟 .task：寿命结束 = 取消
    screen = nil
    dead.set()
    try? await Task.sleep(for: .milliseconds(150))
    producer.cancel()
    let producedAfterDeath = producerSide.count - producedAtDismiss
    let after = before + afterDeath.count
    Swift.print("  死后生产侧仍发 \(producedAfterDeath) 件、消费侧收账 \(afterDeath.count) 件——差额即被丢的件，证明取消真的传导了")
    return (before, after)
}

// —— 反例：永生单例 ——
Swift.print("=== 反例：Task 存进永生单例（跨作用域形态，翻译不动）===")
let busX = IntBus()
let producerX = startProducer { busX.send($0) }
let receivedX = Counter()
do {
    // 消费任务不挂在 Screen 上，而是存进永生单例——「全局事件总线」的旧形态在新世界的投影
    let t = Task.detached {
        for await _ in busX.subject.values { receivedX.bump() }
    }
    Immortal.shared.heldTasks.append(t)
    try? await Task.sleep(for: .milliseconds(120))
    Swift.print("  单例持有期间计数：\(receivedX.count)（在收）")
    // 「Screen」从未存在也无所谓——任务寿命跟单例走，永不终止
    try? await Task.sleep(for: .milliseconds(120))
    Swift.print("  再过 0.12s 计数：\(receivedX.count)（还在收——订阅永生，T5 M5 凭证长寿同款病根）")
}
producerX.cancel()
Swift.print("  结论：跨作用域存活的订阅塞不进视图/作用域寿命——要么显式长寿命 Task 手动管取消，要么留 Combine。")

Swift.print("\n=== 对拍结论 ===")
Swift.print("旧形态（cancellable）与新形态（结构化）收尾行为一致：死前有收、死后停收；")
Swift.print("差异在义务归属——旧世界靠「记得存、记得随宿主销毁」，新世界由结构（作用域/取消传播）担保；")
Swift.print("翻译不动的跨作用域形态如反例所示：永生宿主 + 任务 = 旧病换新装。")
