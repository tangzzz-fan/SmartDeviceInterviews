// T4-Q1 可更新判定清单
import Foundation

let checklist = [
    "模型是否在 Create ML / coremltools 声明为 updatable？",
    "App 是否具备可写模型目录与磁盘预算？",
    "是否有用户同意（个性化/上传样本）？",
    "是否有更新任务失败回滚到旧 .mlmodelc？",
    "是否有端侧验证集防止个性化把准头训崩？",
    "是否评估过『其实该热更云端』？",
]

print("设备端可更新判定清单:")
for (i, item) in checklist.enumerated() {
    print("  [\(i + 1)] \(item)")
}
print("全部「是」才进入实现；否则记拒绝理由")
