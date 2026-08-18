// T5-Q2 延迟度量协议（模拟负载）
import Foundation

func oneShot() -> Double {
    let t0 = CFAbsoluteTimeGetCurrent()
    // 模拟推理
    var x = 0.0
    for i in 0..<50_000 { x += Double(i).squareRoot() }
    _ = x
    return (CFAbsoluteTimeGetCurrent() - t0) * 1000
}

let warmup = 5
let rounds = 20
for _ in 0..<warmup { _ = oneShot() }

var samples: [Double] = []
for _ in 0..<rounds { samples.append(oneShot()) }
samples.sort()
let mean = samples.reduce(0, +) / Double(samples.count)
print("环境: macOS CLI / cpu 模拟负载（非 ANE）")
print(String(format: "暖机 %d 次后正式 %d 次", warmup, rounds))
print(String(format: "mean=%.3f ms  min=%.3f  max=%.3f  p50=%.3f", mean, samples.first!, samples.last!, samples[samples.count / 2]))
