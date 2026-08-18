// T5-Q4 性能报告模板
import Foundation

struct PerfReport {
    let device: String
    let os: String
    let computeUnits: String
    let modelVersion: String
    let meanMs: Double
    let notes: String
}

let report = PerfReport(
    device: "Mac \(ProcessInfo.processInfo.machineHardwareName)",
    os: ProcessInfo.processInfo.operatingSystemVersionString,
    computeUnits: "cpuOnly (CLI)",
    modelVersion: "toy-1.0.0",
    meanMs: 12.3,
    notes: "模拟器/CLI 数字不得写入对外 SLA"
)

print("设备: \(report.device)")
print("系统: \(report.os)")
print("computeUnits: \(report.computeUnits)")
print("模型: \(report.modelVersion)")
print(String(format: "mean: %.2f ms", report.meanMs))
print("备注: \(report.notes)")

extension ProcessInfo {
    var machineHardwareName: String {
        var size = 0
        sysctlbyname("hw.model", nil, &size, nil, 0)
        var model = [CChar](repeating: 0, count: size)
        sysctlbyname("hw.model", &model, &size, nil, 0)
        return String(cString: model)
    }
}
