// T1-Q4b 循环引用对拍 · unowned 翻车版（学员第一版的修复尝试——押错注了）
// 学员当时的判断："回调肯定在对象活着时执行" → 选了 unowned。
// 反例：回调被外部持有、对象先释放，unowned 读取 = 运行时崩溃。
class Fetcher {
    var onComplete: (() -> Void)?

    func start() {
        onComplete = { [unowned self] in print("任务完成", self) }
    }

    deinit { print(">>> Fetcher deinit") }
}

var f: Fetcher? = Fetcher()
f?.start()
let laterCallback = f!.onComplete! // 回调被外部持有（模拟队列里排队的异步任务）
f = nil                            // 对象先行释放 → deinit 打印（环确实解了）
laterCallback()                    // 访问已释放对象的 unowned 引用 → 崩溃，见运行输出
