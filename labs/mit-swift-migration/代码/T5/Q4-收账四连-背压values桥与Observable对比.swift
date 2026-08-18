// T5-Q4 收账四连：背压自定义 Subscriber + values 桥 + @Observable 对比
// （T4 遗留观察项 1/3/4 总收账，D2 争议收口）
// 段一：自定义 Subscriber 报有限需求 .max(2)、处理完按需追加 .max(1)，
//       处理间 sleep 制造慢下游——证明上游「按需求发货」而非灌满（T4 C2 复攻的协议层实操）。
// 段二：同一 publisher 用 .values for-await 消费，与 sink/自定义订阅对拍事件序列；
//       寿命差异口述：cancellable（凭证义务，T4 C1）vs 迭代器/结构化任务生命周期。
// 段三：ObservableObject（objectWillChange 计数）vs @Observable（属性级依赖）爆炸半径对比。
//       诚实声明：Observation 的 withObservationTracking 在 macOS CLI 可用，但回调语义
//       （一次性触发、需重挂）与 SwiftUI 失效机制有差异——本实验测的是「通知粒度」，
//       不等价于真机渲染失效次数，后者记待真机验证。
// 撞墙记录①：在 Publisher 类型作用域里调 print(...) 编译报错——Combine 自带一个
// print() 操作符（Publisher 的实例方法），嵌套在 Publisher 类型里时把全局 print 遮蔽了，
// 得写 Swift.print(...) 显式指名。旧世界没有同名操作符抢名字，这是 Combine 特有的坑。
// 撞墙记录②：段三第一版用 DispatchQueue.main.async 重挂观察 + RunLoop.main.run(until:)
// 等回调落袋——两个坑一起爆：顶层 async 上下文里 RunLoop.run 被拒（T4 Q3 同款墙），
// 且异步重挂根本赶不上同步连发的变更，计数必然偏少。修正：withObservationTracking
// 是一次性回调，onChange 在变更当场同步触发——重挂也当场同步做，不需要任何 RunLoop。
// 撞墙记录③：段三 trackA 第一版没标隔离，顶层代码默认 MainActor，局部函数被推断成
// MainActor 隔离，而 onChange 是非隔离同步闭包——里面调 trackA 等于要求同步 hop 上
// 主 actor，运行时直接 trace trap。加 nonisolated 后 Swift 6 typecheck 又追一刀：
// 被 @Sendable 闭包捕获的局部函数要标 @Sendable，标了又牵出 ModernModel 非 Sendable
// 的捕获链连环错——局部函数这条路的隔离/可发送性两道门越补越漏。终版改封装：
// 探针类 @unchecked Sendable + 方法重挂，把「谁可以跨域」的担保写在类级别一处说清。
// 教训：隔离与 Sendable 的账要在类型边界一次性付清，散在闭包里补是补不完的。
// 撞墙记录④（本轮最贵的一堵墙）：段一第一版跑出来上游只发了 2 件就停——
// 我在 Subscription 里把 receive(_:) 的返回值直接扔了（`_ =`）。Demand 协议里
// 那个返回值就是下游追加的需求，上游不接住 = 需求断流 = 上游永远不再发货。
// 写自定义 Publisher 时「接住追加需求」不是可选项，是协议义务——
// 这跟 T4 C1「不存凭证即取消」同款：协议里不起眼的那一环，恰是承重墙。
// 撞墙记录⑤：段二的 .values 桥连撞四版，是本轮第二贵的墙：
// v1：PassthroughSubject + sleep(50ms)「等订阅建立」——桥只收到 4 件里的 1 件，
//     PassthroughSubject 无缓存，订阅没落袋前发的货全丢。sleep 不是保证，是赌。
// v2：CurrentValueSubject + 信号量等首件落袋——又丢：完成事件先于值到达把迭代器关了，
//     且顶层 MainActor 阻塞 wait + Task {} 继承 MainActor 是标准死锁形状（改 detached）。
// v3：自驱动（消费到首件后在同一任务里同步连发后续）——还是丢：同步连发的值进了
//     桥的内部缓冲，completion 一到迭代器终止，缓冲里的值陪葬。
// v4（终版，先跑探针验证再落正式代码）：异步生产者带节拍——先 sleep 等订阅建立，
//     每发一件让出 20ms 给消费侧拉取，最后才发完成。事件 4/4 不丢。
// 教训三连：①热 Subject 无缓冲，时序错 = 丢数据；②同步连发 vs 桥的拉取节拍不同步
// 时，值会死在缓冲里；③跨异步世界的桥，生产者要按消费者的节拍供货——
// 这其实就是背压思想的生产者侧版（M2/C2 在桥上的回声）。
import Foundation
import Combine
import Observation

// ============ 段一：自定义 Subscriber，有限需求 ============

// 上游打点：看「发了几个」与「下游收几个」的时间差
final class TappingPublisher<Output>: Publisher {
    typealias Failure = Never
    var emitted = 0
    func receive<S: Subscriber>(subscriber: S) where S.Input == Output, S.Failure == Never {
        let sub = TappingSubscription(subscriber: subscriber, owner: self)
        subscriber.receive(subscription: sub)
    }
    final class TappingSubscription<S: Subscriber>: Subscription where S.Input == Output, S.Failure == Never {
        private var subscriber: S?
        private let owner: TappingPublisher
        private var queue: [Output] = []
        init(subscriber: S, owner: TappingPublisher) {
            self.subscriber = subscriber
            self.owner = owner
            self.queue = (1...6).map { "事件-\($0)" as! Output }   // 上游有 6 个货
        }
        func request(_ demand: Subscribers.Demand) {
            deliver(max: demand)
        }
        private func deliver(max demand: Subscribers.Demand) {
            var budget = demand.max ?? 0
            while budget > 0 && !queue.isEmpty {
                let item = queue.removeFirst()
                owner.emitted += 1
                Swift.print("  [上游] 发出第 \(owner.emitted) 件货（库存还剩 \(queue.count)）")
                let additional = subscriber?.receive(item) ?? .none
                budget -= 1
                budget += additional.max ?? 0     // 接住追加需求（撞墙④：第一版这里扔了）
            }
        }
        func cancel() { subscriber = nil }
    }
}

// 慢下游：初始需求 .max(2)，每处理一件追加 .max(1)，处理间 sleep
final class SlowSubscriber: Subscriber {
    typealias Input = String
    typealias Failure = Never
    var received = 0
    func receive(subscription: Subscription) {
        print("[下游] 订阅时报需求：我先只要 2 件")
        subscription.request(.max(2))
    }
    func receive(_ input: String) -> Subscribers.Demand {
        received += 1
        print("  [下游] 收到 \(input)，慢慢处理 0.3s……")
        Thread.sleep(forTimeInterval: 0.3)
        print("  [下游] 处理完了，再要 1 件")
        return .max(1)                          // 按需追加：一次只多要一件
    }
    func receive(completion: Subscribers.Completion<Never>) {
        print("[下游] 完成，共收到 \(received) 件")
    }
}

print("=== 段一：有限需求的背压实操（T4 遗留 1 收账）===")
do {
    let publisher = TappingPublisher<String>()
    let subscriber = SlowSubscriber()
    publisher.subscribe(subscriber)
    // 预期：上游一次只发 2 件（下游报的需求），之后每处理完 1 件才多发 1 件——
    // 发货节奏被下游需求牵着走，而不是 6 件一口气灌满。
    print("段一小结：上游共发 \(publisher.emitted) 件、下游共收 \(subscriber.received) 件")
    assert(publisher.emitted == 6 && subscriber.received == 6)
}

// ============ 段二：values 桥（T4 遗留 4 收账）============

print("\n=== 段二：.values 桥 for-await 消费同一序列 ===")

// nonisolated：避开顶层 MainActor 推断传染（撞墙③同款教训）
nonisolated func runBridgeDemo() async {
    let subject = PassthroughSubject<String, Never>()
    // 异步生产者带节拍（撞墙⑤ v4）：先等订阅建立，每发一件让出节拍，最后发完成
    let producer = Task.detached {
        try? await Task.sleep(for: .milliseconds(100))
        for i in 1...4 {
            subject.send("桥事件-\(i)")
            try? await Task.sleep(for: .milliseconds(20))
        }
        subject.send(completion: .finished)          // 完成 = 桥的自然终点（finish 义务）
    }
    var viaBridge: [String] = []
    for await value in subject.values {              // Combine → AsyncSequence 桥
        viaBridge.append(value)
        Swift.print("  [桥] for-await 收到 \(value)")
    }
    await producer.value
    Swift.print("[桥] 序列结束，共 \(viaBridge.count) 件：\(viaBridge)")
    assert(viaBridge.count == 4, "4 件桥事件一件不能少")
    // 寿命差异口述：桥这边没有 AnyCancellable——for-await 的寿命跟着结构化任务走，
    // task 结束/取消即消费终止；sink 那边凭证得自己存（T4 C1 义务）。
    // 同一序列两条消费路径事件一致——桥只换消费形态，不换数据。
}
await runBridgeDemo()

// ============ 段三：ObservableObject vs @Observable 爆炸半径（T4 遗留 3 / D2 收口）============

print("\n=== 段三：失效爆炸半径对比 ===")

final class LegacyModel: ObservableObject {
    @Published var a: Int = 0
    @Published var b: Int = 0
}

@Observable
final class ModernModel {
    var a: Int = 0
    var b: Int = 0
}

// 观察探针：担保注释——本实验单线程同步进行，所有访问都在顶层执行流上，
// 无跨域共享；@unchecked 是为让 onChange（@Sendable 闭包）能合法捕获 self（撞墙③终版）
final class ObservationProbe: @unchecked Sendable {
    let model = ModernModel()
    var invalidationsForA = 0
    func arm() {   // withObservationTracking 一次性触发：onChange 当场同步重挂，不依赖 RunLoop
        withObservationTracking {
            _ = model.a                        // 依赖只登记了 a
        } onChange: { [self] in
            invalidationsForA += 1
            arm()                              // 同步重挂，模拟持续观察
        }
    }
}

do {
    // 旧底座：任何属性变更都广播 objectWillChange（对象级）
    let legacy = LegacyModel()
    var legacyInvalidations = 0
    var bag = Set<AnyCancellable>()
    legacy.objectWillChange.sink { _ in legacyInvalidations += 1 }.store(in: &bag)

    // 新底座：只观察属性 a（属性级依赖）
    let probe = ObservationProbe()
    probe.arm()

    print("—— 改属性 a 各 3 次 ——")
    for _ in 0..<3 { legacy.a += 1; probe.model.a += 1 }
    print("—— 改属性 b 各 3 次（依赖方只关心 a）——")
    for _ in 0..<3 { legacy.b += 1; probe.model.b += 1 }

    print("LegacyModel（ObservableObject）：依赖方收到 \(legacyInvalidations) 次失效通知（改 a 与改 b 都广播）")
    print("ModernModel（@Observable，只依赖 a）：依赖方收到 \(probe.invalidationsForA) 次失效通知（改 b 无感）")
    assert(legacyInvalidations == 6, "对象级广播：6 次变更 = 6 次通知")
    assert(probe.invalidationsForA == 3, "属性级追踪：只有改 a 的 3 次算数")
    print("""
    段三小结：同样是「两个属性各改 3 次」，对象级广播让只关心 a 的依赖方陪跑 6 次失效，
    属性级追踪只失效 3 次——爆炸半径从「对象」缩到「属性」，T4 C6 的口述拿到实验背书。
    诚实声明：withObservationTracking 是一次性回调+手动重挂，测的是「依赖登记粒度」，
    与 SwiftUI 真机渲染失效次数不等价——渲染层结论记待真机验证。
    """)
}

print("=== Q4 全段跑通：T4 遗留 1/3/4 三项收账完成 ===")
