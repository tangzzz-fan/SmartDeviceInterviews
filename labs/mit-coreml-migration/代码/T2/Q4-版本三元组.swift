// T2-Q4 模型版本三元组约定
import Foundation

struct ModelRelease {
    let modelSemver: String
    let preprocessSemver: String
    let minAppVersion: String
    let labelsHash: String
}

let release = ModelRelease(
    modelSemver: "1.4.0",
    preprocessSemver: "1.2.1",
    minAppVersion: "6.3.0",
    labelsHash: "sha256:toy-labels-v3"
)

print("模型语义版本: \(release.modelSemver)")
print("预处理版本:   \(release.preprocessSemver)")
print("App 最低版本: \(release.minAppVersion)")
print("标签表哈希:   \(release.labelsHash)")
print("约定: 任一字段不匹配 → 拒绝加载或强制走兼容路径，禁止静默错类")
