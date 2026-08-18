// T2-Q3 量化账本 CLI
import Foundation

struct QuantBill {
    let originalMB: Double
    let quantizedMB: Double
    let metricDrop: Double // 绝对掉点，如 Top1 降 0.02 = 2pp
    let latencyGain: Double // 加速比，1.3 = 快 30%

    var sizeSavedRatio: Double { 1.0 - quantizedMB / originalMB }

    var worth: Bool {
        // 教学阈值：体积省 ≥30% 且掉点 ≤2pp 且延迟有收益 → 值得
        sizeSavedRatio >= 0.30 && metricDrop <= 0.02 && latencyGain >= 1.1
    }
}

let bills = [
    QuantBill(originalMB: 40, quantizedMB: 12, metricDrop: 0.015, latencyGain: 1.4),
    QuantBill(originalMB: 40, quantizedMB: 35, metricDrop: 0.01, latencyGain: 1.05),
    QuantBill(originalMB: 40, quantizedMB: 8, metricDrop: 0.08, latencyGain: 1.8),
]

for (i, b) in bills.enumerated() {
    print(
        """
        #\(i + 1) 原\(b.originalMB)MB → \(b.quantizedMB)MB (省 \(String(format: "%.0f", b.sizeSavedRatio * 100))%) \
        掉点 \(b.metricDrop) 加速 \(b.latencyGain)x → \(b.worth ? "值得" : "不值得")
        """
    )
}
print("阈值可改，但必须显式；禁止「感觉差不多就量化」")
