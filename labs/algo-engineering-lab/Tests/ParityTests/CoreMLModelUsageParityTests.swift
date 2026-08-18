import XCTest
@testable import AlgoSwift

#if canImport(CoreML)
import CoreML

final class CoreMLModelUsageParityTests: XCTestCase {
    func testSwiftCanLoadAndRunPythonGeneratedModel() throws {
        let modelURL = try Self.locate("artifacts/coreml/activity_fp32.mlpackage")
        let reportURL = try Self.locate("golden/coreml_quant/compare_report.json")

        let reportData = try Data(contentsOf: reportURL)
        let report = try JSONSerialization.jsonObject(with: reportData) as? [String: Any]
        let preprocess = report?["preprocess"] as? [String: Any]
        let mean = (preprocess?["mean"] as? [Double]) ?? []
        let scale = (preprocess?["scale"] as? [Double]) ?? []
        XCTAssertEqual(mean.count, 8)
        XCTAssertEqual(scale.count, 8)

        // raw 特征 -> 使用 Python 报告里的 scaler 参数归一化，确保 Swift 与 Python 同口径
        let raw: [Double] = [0.1, -0.2, 0.3, 0.1, -0.1, 0.2, 0.0, 0.05]
        let scaled = zip(zip(raw, mean), scale).map { (pair, s) in
            let (x, m) = pair
            return (x - m) / s
        }

        let session = try CoreMLActivityModel.load(modelURL: modelURL, computeUnits: .cpuOnly)
        let probs = try session.predict(features: scaled)
        XCTAssertEqual(probs.count, 3)
        XCTAssertTrue(probs.allSatisfy { $0.isFinite })
        let sum = probs.reduce(0, +)
        XCTAssertEqual(sum, 1.0, accuracy: 1e-3)
        let top = probs.enumerated().max(by: { $0.element < $1.element })?.offset ?? -1
        XCTAssertTrue((0..<3).contains(top))
    }

    func testSwiftOutputsMatchPythonExpectedVectors() throws {
        let modelFP32 = try Self.locate("artifacts/coreml/activity_fp32.mlpackage")
        let modelFP16 = try Self.locate("artifacts/coreml/activity_fp16.mlpackage")
        let reportURL = try Self.locate("golden/coreml_quant/compare_report.json")
        let reportData = try Data(contentsOf: reportURL)
        guard let report = try JSONSerialization.jsonObject(with: reportData) as? [String: Any],
              let vectors = report["verification_vectors"] as? [String: Any],
              let scaled = vectors["scaled_features"] as? [[Double]],
              let exp32 = vectors["expected_probs_fp32"] as? [[Double]],
              let exp16 = vectors["expected_probs_fp16"] as? [[Double]],
              let tol32 = vectors["tolerance_fp32_abs"] as? Double,
              let tol16 = vectors["tolerance_fp16_abs"] as? Double else {
            XCTFail("verification_vectors missing in compare_report.json")
            return
        }

        XCTAssertEqual(scaled.count, exp32.count)
        XCTAssertEqual(scaled.count, exp16.count)

        // T14：同一 Session 缓存下多次 predict，仍须对齐 Python 期望
        let session32 = try CoreMLActivityModel.load(modelURL: modelFP32, computeUnits: .cpuOnly)
        let session16 = try CoreMLActivityModel.load(modelURL: modelFP16, computeUnits: .cpuOnly)

        for i in 0..<scaled.count {
            let got32 = try session32.predict(features: scaled[i])
            let got16 = try session16.predict(features: scaled[i])
            XCTAssertEqual(got32.count, exp32[i].count, "fp32 vector \(i) length")
            XCTAssertEqual(got16.count, exp16[i].count, "fp16 vector \(i) length")
            for j in 0..<got32.count {
                XCTAssertEqual(got32[j], exp32[i][j], accuracy: tol32, "fp32[\(i)][\(j)]")
            }
            for j in 0..<got16.count {
                XCTAssertEqual(got16[j], exp16[i][j], accuracy: tol16, "fp16[\(i)][\(j)]")
            }
        }
    }

    private static func locate(_ relative: String) throws -> URL {
        var url = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<8 {
            let candidate = url.appendingPathComponent(relative)
            if FileManager.default.fileExists(atPath: candidate.path) {
                return candidate
            }
            url.deleteLastPathComponent()
        }
        XCTFail("cannot locate \(relative)")
        throw NSError(domain: "CoreMLModelUsage", code: 1)
    }
}
#else
final class CoreMLModelUsageParityTests: XCTestCase {
    func testSkipWhenCoreMLUnavailable() throws {
        throw XCTSkip("CoreML unavailable on this platform")
    }
}
#endif
