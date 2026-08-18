// T3-Q4 管线三段耗时
import Foundation

func timed(_ name: String, _ work: () -> Void) -> Double {
    let t0 = CFAbsoluteTimeGetCurrent()
    work()
    let ms = (CFAbsoluteTimeGetCurrent() - t0) * 1000
    print(String(format: "%@ %.2f ms", name, ms))
    return ms
}

let pre = timed("preprocess") { Thread.sleep(forTimeInterval: 0.01) }
let inf = timed("infer     ") { Thread.sleep(forTimeInterval: 0.03) }
let post = timed("postprocess") { Thread.sleep(forTimeInterval: 0.005) }
print(String(format: "total %.2f ms (模拟；真模型请替换 sleep 为真实调用并标注设备)", pre + inf + post))
