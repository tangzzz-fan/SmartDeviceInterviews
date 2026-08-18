import Foundation
import CoreML

/// 滤波窗 → 活动分类用的 8 维特征（与 Python `generate_coreml_streaming` 同口径）。
public enum WindowActivityFeatures {
    public static let windowSize = 25
    public static let featureCount = 8

    public static func extract(_ y: [Double]) throws -> [Double] {
        guard y.count == windowSize else { throw AlgoError.invalidArgument }
        let mean = y.reduce(0, +) / Double(y.count)
        let varSum = y.reduce(0.0) { $0 + ($1 - mean) * ($1 - mean) }
        let std = sqrt(varSum / Double(y.count))
        let ymin = y.min() ?? 0
        let ymax = y.max() ?? 0
        let energy = y.reduce(0.0) { $0 + $1 * $1 } / Double(y.count)
        let first = y[0]
        let last = y[y.count - 1]
        let mid = y[y.count / 2]
        return [mean, std, ymax - ymin, energy, first, last, abs(last - first), mid]
    }

    public static func scale(
        _ features: [Double],
        mean: [Double],
        scale: [Double]
    ) throws -> [Double] {
        guard features.count == featureCount,
              mean.count == featureCount,
              scale.count == featureCount else {
            throw AlgoError.invalidArgument
        }
        return zip(zip(features, mean), scale).map { pair, s in
            let (x, m) = pair
            return (x - m) / s
        }
    }
}

/// BLE 分片 → StreamingFIR → 窗特征 → StandardScaler → CoreML Session。
public final class CoreMLStreamingPipeline {
    private let fir: StreamingFIRPipeline
    private let session: CoreMLActivityModel.Session
    private let mean: [Double]
    private let scale: [Double]

    public private(set) var featureWindows: [[Double]] = []
    public private(set) var probabilityWindows: [[Double]] = []

    public init(
        session: CoreMLActivityModel.Session,
        mean: [Double],
        scale: [Double],
        ringCapacity: Int = 50,
        windowSize: Int = WindowActivityFeatures.windowSize,
        gapPolicy: GapPolicy = .zeroFill,
        samplesPerMissingPacket: Int = 2
    ) {
        self.session = session
        self.mean = mean
        self.scale = scale
        self.fir = StreamingFIRPipeline(
            ringCapacity: ringCapacity,
            windowSize: windowSize,
            gapPolicy: gapPolicy,
            samplesPerMissingPacket: samplesPerMissingPacket
        )
    }

    public func ingest(_ packet: BLEPacket) throws {
        let before = fir.outputs.count
        try fir.ingest(packet)
        for i in before..<fir.outputs.count {
            let feats = try WindowActivityFeatures.extract(fir.outputs[i])
            let scaled = try WindowActivityFeatures.scale(feats, mean: mean, scale: scale)
            let probs = try session.predict(features: scaled)
            featureWindows.append(feats)
            probabilityWindows.append(probs)
        }
    }
}

/// 串行推理 Actor：BLE 回调线程把包交给 Actor，避免并发触碰同一 Session。
public actor CoreMLStreamingInferenceActor {
    private let pipeline: CoreMLStreamingPipeline

    public init(pipeline: CoreMLStreamingPipeline) {
        self.pipeline = pipeline
    }

    public func ingest(_ packet: BLEPacket) throws {
        try pipeline.ingest(packet)
    }

    public func probabilityWindows() -> [[Double]] {
        pipeline.probabilityWindows
    }

    public func featureWindows() -> [[Double]] {
        pipeline.featureWindows
    }
}
