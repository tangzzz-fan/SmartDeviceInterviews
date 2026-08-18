// T1-Q4a 循环引用对拍 · 泄漏版（学员第一版）
// 场景：模拟异步回调存进属性——环的两条边：self → onComplete 属性 → 闭包强捕获 self
class Fetcher {
    var onComplete: (() -> Void)?

    func start() {
        // 默认强捕获 self：和 OC block 不带 __weak 一模一样
        onComplete = { print("任务完成", self) }
    }

    deinit { print(">>> Fetcher deinit（出现 = 已释放）") }
}

var f: Fetcher? = Fetcher()
f?.start()
f = nil // 引用置空；若上面不打印 deinit，说明环把它扣住了
print("已置 nil —— 看上面有没有 deinit 输出（泄漏版：没有）")
