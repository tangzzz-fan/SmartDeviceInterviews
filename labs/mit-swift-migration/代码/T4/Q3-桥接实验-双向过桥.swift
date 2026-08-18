// T4-Q3 桥接实验：Combine ↔ async 双向过桥（挂载体 4.4 前置）
// 桥 A（流→单值）：publisher 经 .first() + withCheckedContinuation 拉平成 async 函数。
// 桥 B（async→流）：async 轮询包成 AsyncStream，与 Timer.publish + sink 双实现输出对拍。
// 撞墙记录：桥 A 第一版把 sink 的凭证声明成 continuation 闭包里的局部变量、没 store——
// 闭包一返回凭证就 deinit，订阅当场取消，await 永远挂住（跟 Q2 对照组同款死法，只是后果更重：
// Q2 是收不到事件，这里是欠条永远没人兑现、调用方挂死）。补进全局 bag 才通。
// 教训复用：T3 说「欠条必须兑现」，T4 补上「兑现之前桥本身也得活着」——凭证寿命是桥的承重墙。
// 撞墙记录②：顶层直接写 RunLoop.main.run 驱动 Timer——编译器警告 unavailable from
// asynchronous contexts（Swift 6 直接报错）：顶层 await 代码整体在 async 上下文里，
// 而 RunLoop 是同步世界的驱动方式，两个世界的调度器不能直接混用。把驱动逻辑挪进
// 同步函数 runTimerWorld()，才从 async 上下文脱身。教训：桥不光接数据，还接「调度世界」。
import Foundation
import Combine

let start = Date()
func ts() -> String { String(format: "%.2fs", Date().timeIntervalSince(start)) }

// ---- 桥 A：Combine → async（单值拉平）----
func oneShot(_ q: String) -> AnyPublisher<[String], Never> {
    Deferred {
        Future<[String], Never> { promise in
            DispatchQueue.global().asyncAfter(deadline: .now() + 0.2) {
                promise(.success(["\(q)-hit"]))
            }
        }
    }
    .eraseToAnyPublisher()
}

var bridgeBag = Set<AnyCancellable>()   // 桥的承重墙：凭证必须活到欠条兑现

func searchOnce(_ q: String) async -> [String] {
    await withCheckedContinuation { cont in
        oneShot(q)
            .first()
            .sink { cont.resume(returning: $0) }
            .store(in: &bridgeBag)      // 不存 = 订阅取消 = 欠条无人兑现
    }
}

// ---- 桥 B：async → 流（AsyncStream 包轮询）----
func pollValue(_ i: Int) async -> String {
    try? await Task.sleep(nanoseconds: 200_000_000)
    return "beat-\(i)"
}

let stream = AsyncStream<String> { continuation in
    Task {
        for i in 1...5 {
            continuation.yield(await pollValue(i))
        }
        continuation.finish()   // 终止义务：不调 finish，for-await 永远不退出
    }
}

// ---- 跑桥 A ----
print("[\(ts())] 桥 A：await 发起")
let result = await searchOnce("combine")
print("[\(ts())] 桥 A：拿到 \(result)（0.2s 后兑现，async 世界消费 Combine 管道）")

// ---- 跑桥 B 的 async 侧 ----
print("[\(ts())] 桥 B-async：for-await 开始")
var asyncBeats: [String] = []
for await v in stream {
    asyncBeats.append(v)
    print("[\(ts())] 桥 B-async：\(v)")
}
print("[\(ts())] 桥 B-async：流结束（finish 被调用，for-await 正常退出）")

// ---- 跑桥 B 的 Combine 侧（Timer.publish 对照实现，同步世界里驱动）----
var timerBeats: [String] = []

func runTimerWorld() {
    var timerBag = Set<AnyCancellable>()
    let timerStart = Date()
    Timer.publish(every: 0.2, on: .main, in: .common)
        .autoconnect()
        .prefix(5)
        .scan(0) { n, _ in n + 1 }
        .sink { i in
            let v = "beat-\(i)"
            timerBeats.append(v)
            print(String(format: "[%.2fs] 桥 B-Combine：%@", Date().timeIntervalSince(timerStart), v))
        }
        .store(in: &timerBag)

    let deadline = Date().addingTimeInterval(1.5)
    while Date() < deadline { RunLoop.main.run(mode: .default, before: deadline) }
}

runTimerWorld()

// ---- 对拍 ----
assert(asyncBeats == timerBeats, "两侧输出应一致：\(asyncBeats) vs \(timerBeats)")
print("对拍通过：AsyncStream 与 Timer.publish 两份输出一致 \(asyncBeats)")
print("寿命语义差异：async 侧没有任何 AnyCancellable——for-await 的寿命就是流的寿命（结构化）；")
print("Combine 侧靠 timerBag 持有凭证，漏存即 Q2 同款死法。")
