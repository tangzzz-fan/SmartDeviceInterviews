import Foundation
import CoreML

// MARK: - CoreML 集成模式演示
//
// 配合 docs/09-CoreML入门/06-CoreML与Swift集成模式.md 使用。
// 本文件演示三种常见的 CoreML 集成模式及其适用场景。
// **验证性代码，非生产组件**——目的是让初学者看到 API 怎么用。

/// 模式 1：最简路径（理解用，不推荐生产）
///
/// 每次调用都 compile + load + predict。
/// 适合一次性离线工具或 playground 实验，不适合热路径。
///
/// 类比：每次做饭都重新搭灶台——能吃到饭，但太慢了。
public enum SimpleOneShot {

    /// 一次性推理：给 8 维特征，返回 3 类概率。
    ///
    /// ```swift
    /// let probs = try SimpleOneShot.predict(
    ///     modelURL: packageURL,
    ///     scaledFeatures: [0.1, -0.2, 0.3, ...]
    /// )
    /// print("top-1:", probs.enumerated().max(by: { $0.element < $1.element })!.offset)
    /// ```
    ///
    /// - Warning: 每次调用含 compile，延迟约 40ms+，禁止用于热路径。
    public static func predict(
        modelURL: URL,
        scaledFeatures: [Double]
    ) throws -> [Double] {
        // Step 1: 编译（≈40ms，最贵的一步）
        let compiledURL = try MLModel.compileModel(at: modelURL)

        // Step 2: 加载
        let model = try MLModel(contentsOf: compiledURL)

        // Step 3: 构造输入
        let inputArray = try MLMultiArray(shape: [1, 8], dataType: .float32)
        for i in 0..<min(scaledFeatures.count, 8) {
            inputArray[i] = NSNumber(value: Float(scaledFeatures[i]))
        }

        // Step 4: 推理
        let inputName = model.modelDescription.inputDescriptionsByName.keys.first ?? "features"
        let provider = try MLDictionaryFeatureProvider(dictionary: [inputName: inputArray])
        let output = try model.prediction(from: provider)

        // Step 5: 读取输出
        let outputName = model.modelDescription.outputDescriptionsByName.keys.first ?? "softmax_0"
        guard let outArray = output.featureValue(for: outputName)?.multiArrayValue else {
            throw AlgoError.invalidArgument
        }
        return (0..<outArray.count).map { outArray[$0].doubleValue }
    }
}

// MARK: - 模式 2：Session 缓存（本 lab 推荐）

/// 模式 2：Session 缓存模式
///
/// compile 一次、缓存 MLModel、反复 predict。这是本 lab 推荐的生产路径。
///
/// 类比：灶台搭好不拆，每次做饭只管炒菜。
///
/// 对应本 lab 的 `CoreMLActivityModel.load → Session.predict`。
///
/// ```swift
/// // App 启动时
/// let session = try CachedSession(modelURL: packageURL)
///
/// // 热路径反复调用
/// let probs = try session.predict(scaledFeatures: features)
/// ```
public final class CachedSession {
    private let model: MLModel
    private let inputName: String
    private let outputName: String

    /// 初始化时执行编译和加载（应在启动 / 后台线程完成）。
    ///
    /// - Parameters:
    ///   - modelURL: `.mlpackage` 路径。
    ///   - computeUnits: 硬件后端偏好。默认 `.all`。
    public init(
        modelURL: URL,
        computeUnits: MLComputeUnits = .all
    ) throws {
        let compiledURL = try MLModel.compileModel(at: modelURL)
        let config = MLModelConfiguration()
        config.computeUnits = computeUnits
        self.model = try MLModel(contentsOf: compiledURL, configuration: config)
        self.inputName = model.modelDescription.inputDescriptionsByName.keys.first ?? "features"
        self.outputName = model.modelDescription.outputDescriptionsByName.keys.first ?? "softmax_0"
    }

    /// 纯推理（热路径）：已 scaled 的 8 维特征 → 3 类概率。
    public func predict(scaledFeatures: [Double]) throws -> [Double] {
        guard scaledFeatures.count == 8 else { throw AlgoError.invalidArgument }

        let inputArray = try MLMultiArray(shape: [1, 8], dataType: .float32)
        for i in 0..<8 {
            inputArray[i] = NSNumber(value: Float(scaledFeatures[i]))
        }
        let provider = try MLDictionaryFeatureProvider(dictionary: [inputName: inputArray])
        let output = try model.prediction(from: provider)
        guard let outArray = output.featureValue(for: outputName)?.multiArrayValue else {
            throw AlgoError.invalidArgument
        }
        return (0..<outArray.count).map { outArray[$0].doubleValue }
    }

    /// 辅助：获取 top-1 类别名和置信度。
    public func classifyTopOne(
        scaledFeatures: [Double],
        classNames: [String] = ["rest", "walk", "run"]
    ) throws -> (className: String, confidence: Double) {
        let probs = try predict(scaledFeatures: scaledFeatures)
        let maxIdx = probs.enumerated().max(by: { $0.element < $1.element })!.offset
        return (classNames[maxIdx], probs[maxIdx])
    }
}

// MARK: - 模式 3：Actor 隔离（BLE 回调场景）

/// 模式 3：Actor 隔离模式
///
/// BLE 回调可能从不同线程到来，直接触碰 Session 可能导致不确定性延迟。
/// 用 Swift Actor 把推理串行化。
///
/// 类比：餐厅只有一个厨师（Session），服务员（BLE 回调）排队下单，厨师按顺序炒。
///
/// 对应本 lab 的 `CoreMLStreamingInferenceActor`。
///
/// ```swift
/// let actor = try InferenceActor(modelURL: packageURL)
///
/// // BLE 回调线程 1
/// Task { let p = try await actor.predict(scaledFeatures: features1) }
///
/// // BLE 回调线程 2
/// Task { let p = try await actor.predict(scaledFeatures: features2) }
/// ```
public actor InferenceActor {
    private let session: CachedSession

    public init(
        modelURL: URL,
        computeUnits: MLComputeUnits = .all
    ) throws {
        self.session = try CachedSession(modelURL: modelURL, computeUnits: computeUnits)
    }

    /// 串行推理：即使多个线程同时调用，Actor 保证一次只执行一个。
    public func predict(scaledFeatures: [Double]) throws -> [Double] {
        try session.predict(scaledFeatures: scaledFeatures)
    }

    public func classifyTopOne(
        scaledFeatures: [Double],
        classNames: [String] = ["rest", "walk", "run"]
    ) throws -> (className: String, confidence: Double) {
        try session.classifyTopOne(scaledFeatures: scaledFeatures, classNames: classNames)
    }
}

// MARK: - 模式对比表（文档引用）

/*
 ┌─────────────────┬──────────────┬──────────────┬──────────────────┐
 │ 对比项           │ 模式 1       │ 模式 2       │ 模式 3           │
 │                 │ SimpleOneShot│ CachedSession│ InferenceActor   │
 ├─────────────────┼──────────────┼──────────────┼──────────────────┤
 │ 每次含 compile？ │ ✅ 是        │ ❌ 否        │ ❌ 否            │
 │ 线程安全？       │ 无状态       │ MLModel 安全 │ Actor 串行保证    │
 │ 推理延迟 (p50)  │ ~42ms        │ ~0.04ms      │ ~0.04ms + 队列   │
 │ 适用场景        │ 一次性工具    │ 通用生产      │ BLE 多回调        │
 │ 本 lab 对应     │ predictProb  │ Session      │ StreamingActor   │
 └─────────────────┴──────────────┴──────────────┴──────────────────┘
 */
