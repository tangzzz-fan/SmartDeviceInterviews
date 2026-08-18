// T5-Q1 computeUnits 选项说明
import Foundation
import CoreML

let units: [(MLComputeUnits, String)] = [
    (.cpuOnly, "可复现、调试友好；无 GPU/ANE"),
    (.cpuAndGPU, "常见加速；仍可能不上 ANE"),
    (.all, "允许 Neural Engine；真机才有意义"),
    (.cpuAndNeuralEngine, "跳过 GPU；部分机型/模型路径"),
]

print("MLComputeUnits:")
for (u, note) in units {
    print("  \(u.rawValue): \(note)")
}
print("默认别盲选 .all；用度量说话，并标注设备")
