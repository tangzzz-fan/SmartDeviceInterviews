// T3-Q3 VNCoreML / 编译失败骨架
import Foundation
import CoreML
import Vision

func tryMakeVisionModel(from path: String) {
    let url = URL(fileURLWithPath: path)
    do {
        let compiled = try MLModel.compileModel(at: url)
        let model = try MLModel(contentsOf: compiled)
        _ = try VNCoreMLModel(for: model)
        print("成功（意外）")
    } catch {
        print("VNCoreML 管线失败（预期）: \(error.localizedDescription)")
        print("处理建议: 区分『文件不存在』『编译失败』『模型无 Vision 兼容输入』三层")
    }
}

tryMakeVisionModel(from: "/tmp/mit-coreml-not-exist.mlmodel")
