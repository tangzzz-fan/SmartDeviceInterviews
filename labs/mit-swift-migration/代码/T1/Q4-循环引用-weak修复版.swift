// T1-Q4c 循环引用对拍 · weak 修复版（复攻版）
// 教训：闭包寿命不确定 → weak（自动变 nil）；unowned 只用于"闭包必然不晚于对象死"的场景。
class Fetcher {
    var onComplete: (() -> Void)?

    func start() {
        onComplete = { [weak self] in
            guard let self else {
                print("回调触发时对象已释放，安全退出（不崩）")
                return
            }
            print("任务完成", self)
        }
    }

    deinit { print(">>> Fetcher deinit") }
}

var f: Fetcher? = Fetcher()
f?.start()
let laterCallback = f!.onComplete!
f = nil          // 预期：deinit 打印（环被 weak 打断）
laterCallback()  // 预期：安全退出分支，不崩
print("weak 修复验证完成：deinit 出现 + 迟到回调安全着陆")
