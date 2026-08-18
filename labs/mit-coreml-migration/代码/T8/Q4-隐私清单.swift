// T8-Q4 权限与隐私检查清单
import Foundation

let items = [
    ("NSCameraUsageDescription 权限文案", true),
    ("on-device 处理声明（默认不出设备）", true),
    ("数据不出设备（隐私说明）", true),
    ("分析结果生命周期管理", true),
    ("与自定义 CoreML 数据流差异说明（模型/输入/输出在哪侧）", true),
]
for (name, ok) in items {
    print("\(ok ? "[通过]" : "[缺项]") \(name)")
}
print("说明: VisionKit/DataScanner 默认 on-device；自定义 CoreML 同样 on-device 但需自证（T5 C6 威胁模型）。")
