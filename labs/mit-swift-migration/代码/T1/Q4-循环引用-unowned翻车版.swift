// T1-Q4b 循环引用对拍 · unowned 翻车版（学员第一版的修复尝试——押错注了）
//
// 【预期行为】本文件运行必崩（SIGABRT / exit ≠ 0）。崩即成功，不是环境坏了。
// 学员当时的判断："回调肯定在对象活着时执行" → 选了 unowned。
// 反例：回调被外部持有、对象先释放，unowned 读取 = 运行时崩溃。
//
// 对拍：同目录 Q4-泄漏版（环不解）/ Q4-weak修复版（安全解环）/ 本文件（解环但崩）。
// 跑法：`swift Q4-循环引用-unowned翻车版.swift` —— 看到 deinit 后再崩，即验证成立。

class Fetcher {
    var onComplete: (() -> Void)?

    func start() {
        onComplete = { [unowned self] in
            print("任务完成", self)
        }
    }

    deinit { print(">>> Fetcher deinit") }
}

print("【预期崩溃演示】解环成功后访问已释放对象的 unowned 引用")
var f: Fetcher? = Fetcher()
f?.start()
let laterCallback = f!.onComplete! // 回调被外部持有（模拟队列里排队的异步任务）
f = nil                            // 对象先行释放 → deinit 打印（环确实解了）
print("即将调用 laterCallback —— 下一行应崩溃")
laterCallback()                    // 访问已释放对象的 unowned 引用 → 崩溃
