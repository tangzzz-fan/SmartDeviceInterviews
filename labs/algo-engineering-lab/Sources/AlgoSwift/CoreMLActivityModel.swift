import Foundation
import CoreML

/// 读取 Python 生成的 CoreML `.mlpackage` 并在 Swift 侧执行推理。
///
/// - 推荐：`load` 一次拿到 `Session`，再反复 `predict`（T14）。
/// - `predictProbabilities` 每次都会 compile，仅适合偶发调用或对照基准。
public enum CoreMLActivityModel {
    public final class Session {
        private let model: MLModel
        private let inputName: String
        private let outputName: String

        fileprivate init(model: MLModel) {
            self.model = model
            self.inputName = model.modelDescription.inputDescriptionsByName.keys.first ?? "features"
            self.outputName = model.modelDescription.outputDescriptionsByName.keys.first ?? "softmax_0"
        }

        /// 纯推理：已 scaled 的 8 维特征 → 三类概率。
        public func predict(features: [Double]) throws -> [Double] {
            guard features.count == 8 else { throw AlgoError.invalidArgument }

            let shape = [1, 8] as [NSNumber]
            let inputArray = try MLMultiArray(shape: shape, dataType: .float32)
            for i in 0..<8 {
                inputArray[i] = NSNumber(value: Float(features[i]))
            }
            let provider = try MLDictionaryFeatureProvider(dictionary: [inputName: inputArray])
            let out = try model.prediction(from: provider)
            guard let outArray = out.featureValue(for: outputName)?.multiArrayValue else {
                throw AlgoError.invalidArgument
            }
            var probs = [Double]()
            probs.reserveCapacity(outArray.count)
            for i in 0..<outArray.count {
                probs.append(outArray[i].doubleValue)
            }
            return probs
        }
    }

    /// 编译一次并加载模型（应缓存 `Session`）。
    public static func load(
        modelURL: URL,
        computeUnits: MLComputeUnits = .all
    ) throws -> Session {
        let compiledURL = try MLModel.compileModel(at: modelURL)
        let config = MLModelConfiguration()
        config.computeUnits = computeUnits
        let model = try MLModel(contentsOf: compiledURL, configuration: config)
        return Session(model: model)
    }

    /// 兼容旧路径：每次调用都 compile + load + predict（对照 bench 用）。
    public static func predictProbabilities(
        modelURL: URL,
        features: [Double],
        computeUnits: MLComputeUnits = .all
    ) throws -> [Double] {
        let session = try load(modelURL: modelURL, computeUnits: computeUnits)
        return try session.predict(features: features)
    }
}
