// T3-Q2 可取消的并发下载 Gallery（挂载体 3.2 本体，T2 取消语义回收）
// 思路：cancelAll 只是「插旗」，任务停不停看它配不配合检查——两轮对拍。
// 撞墙记录：第一版两轮都写 try await Task.sleep，结果第一轮也全被取消了，
// 百思不得其解——原来 Task.sleep 本身就是响应取消的检查点（被取消时抛错）。
// 要模拟「不配合」，得用 try? 吞掉睡眠里的取消信号、且不调 checkCancellation。
// 教训：旗子其实处处在，缺的是「看一眼」的协作。
import Foundation

func download(_ id: Int, cooperative: Bool) async throws -> String {
    for chunk in 1...4 {
        if cooperative {
            try await Task.sleep(nanoseconds: 300_000_000) // sleep 自身响应取消（抛 CancellationError）
            try Task.checkCancellation()                   // 显式检查点
        } else {
            try? await Task.sleep(nanoseconds: 300_000_000) // 吞掉取消信号 = 不协作
        }
        print("  [download \(id)] chunk \(chunk)/4")
    }
    return "img-\(id)"
}

func galleryRound(cooperative: Bool, label: String) async {
    print("=== \(label) ===")
    let roundStart = Date()
    var done = 0, cancelled = 0
    await withTaskGroup(of: Result<String, Error>.self) { group in
        for id in 1...5 {
            group.addTask {
                do { return .success(try await download(id, cooperative: cooperative)) }
                catch { return .failure(error) }
            }
        }
        try? await Task.sleep(nanoseconds: 500_000_000) // 让下载跑 0.5s 再插旗
        group.cancelAll()
        print("  —— cancelAll 插旗 ——")
        for await result in group {
            switch result {
            case .success(let name): done += 1; print("  完成：\(name)")
            case .failure: cancelled += 1
            }
        }
    }
    print(String(format: "  结果：完成 %d / 取消 %d（耗时 %.2fs）", done, cancelled, Date().timeIntervalSince(roundStart)))
    if cooperative {
        assert(cancelled == 5 && done == 0, "协作版应全部在检查点了结")
    } else {
        assert(done == 5 && cancelled == 0, "不协作版旗子无效、全部跑完")
    }
}

await galleryRound(cooperative: false, label: "第一轮：不协作版（不看旗子）")
await galleryRound(cooperative: true, label: "第二轮：协作版（检查点看旗子）")
print("Q2 验证通过：取消 = 旗子传播 + 协作了结；不检查就取消不掉")
