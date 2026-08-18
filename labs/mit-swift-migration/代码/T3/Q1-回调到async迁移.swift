// T3-Q1 回调 → async 迁移（挂载体 3.1 本体）
// 思路：OC 风 completion API 用 continuation 桥成 async——continuation 是一次性「欠条」。
// 撞墙记录：第一版我用 withCheckedContinuation + resume(returning: result)，把整个
// Result 当值还回去了，调用点拿到的是 Result<User, Error> 而不是 User——
// 才反应过来：要把 Result 摊平成 throws，得用 withCheckedThrowingContinuation + resume(with:)。
import Foundation

struct User { let id: Int; let name: String }
struct NetworkError: Error, CustomStringConvertible {
    var description: String { "NetworkError(id 非法)" }
}

// ---- OC 风回调 API（迁移靶子）----
func fetchUserCallback(id: Int, completion: @escaping (Result<User, Error>) -> Void) {
    DispatchQueue.global().asyncAfter(deadline: .now() + 0.5) {
        if id > 0 {
            completion(.success(User(id: id, name: "Ada")))
        } else {
            completion(.failure(NetworkError()))
        }
    }
}

// ---- 桥接版：欠条只能兑现一次，成功/失败两条路都必须兑现 ----
func fetchUser(id: Int) async throws -> User {
    try await withCheckedThrowingContinuation { continuation in
        fetchUserCallback(id: id) { result in
            continuation.resume(with: result) // Result 摊平：success→return，failure→throw
        }
    }
}

// ---- 时间线证据：await 期间主流程挂起，但心跳任务活着 = 线程没被堵 ----
let start = Date()
func stamp(_ msg: String) {
    print(String(format: "t=%.2fs  %@", Date().timeIntervalSince(start), msg))
}

let heartbeat = Task { @MainActor in
    while !Task.isCancelled {
        stamp("❤️ 心跳（等待者挂着，我还活着——证明挂起不阻塞）")
        try? await Task.sleep(nanoseconds: 150_000_000)
    }
}

stamp("发起 fetchUser(id: 7)（模拟网络延迟 0.5s）")
let ada = try await fetchUser(id: 7)
stamp("拿到 \(ada.name)——await 让异步代码长得像同步")

// 失败路也必须兑现：id 非法 → 错误经 throws 传回（OC 时代靠 completion 里判 error）
do {
    _ = try await fetchUser(id: -1)
    stamp("不该走到这里")
} catch {
    stamp("失败路也桥通了：\(error)")
}

heartbeat.cancel()
print("Q1 验证通过：回调→async 桥接成立；挂起≠阻塞；成败两路都兑现恰好一次")
