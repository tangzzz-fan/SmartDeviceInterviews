// T1-Q2 模型加载失败路径
import Foundation
import CoreML

func loadModel(at path: String) {
    let url = URL(fileURLWithPath: path)
    do {
        let config = MLModelConfiguration()
        config.computeUnits = .cpuOnly
        let model = try MLModel(contentsOf: url, configuration: config)
        print("意外成功: \(model.modelDescription)")
    } catch {
        print("加载失败（预期）: \(error.localizedDescription)")
        print("诊断分层: 资源缺失 → 检查 Bundle/下载；不要当「模型算错」重试")
    }
}

print("=== 不存在的路径 ===")
loadModel(at: "/tmp/mit-coreml-definitely-missing.mlmodelc")

print("\n=== 空文件伪装 ===")
let fake = FileManager.default.temporaryDirectory.appendingPathComponent("empty.mlmodelc")
try? FileManager.default.createDirectory(at: fake, withIntermediateDirectories: true)
loadModel(at: fake.path)
try? FileManager.default.removeItem(at: fake)
