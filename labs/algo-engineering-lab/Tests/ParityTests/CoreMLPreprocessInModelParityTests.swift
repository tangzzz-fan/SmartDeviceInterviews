import XCTest
@testable import AlgoSwift

#if canImport(CoreML)
import CoreML

/// T15：App 侧 scaler vs 入模预处理；双重 normalize 负例。
final class CoreMLPreprocessInModelParityTests: XCTestCase {
    func testAppSideMatchesInModelAndDoubleNormalizeDiverges() throws {
        let reportURL = try Self.locate("golden/coreml_preprocess_inmodel/compare_report.json")
        let reportData = try Data(contentsOf: reportURL)
        guard let report = try JSONSerialization.jsonObject(with: reportData) as? [String: Any],
              let vectors = report["verification_vectors"] as? [String: Any],
              let raw = vectors["raw_features"] as? [[Double]],
              let scaled = vectors["scaled_features"] as? [[Double]],
              let doubleScaled = vectors["double_scaled_features"] as? [[Double]],
              let expApp = vectors["expected_probs_app_side"] as? [[Double]],
              let expIn = vectors["expected_probs_in_model"] as? [[Double]],
              let tol = vectors["tolerance_abs"] as? Double,
              let minDoubleDiff = vectors["double_normalize_min_max_abs_diff"] as? Double,
              let models = report["models"] as? [String: Any],
              let appRel = models["app_side_scaled"] as? String,
              let inRel = models["in_model_preprocess"] as? String else {
            XCTFail("malformed compare_report.json")
            return
        }

        let appURL = try Self.locate(appRel)
        let inURL = try Self.locate(inRel)
        let sessionApp = try CoreMLActivityModel.load(modelURL: appURL, computeUnits: .cpuOnly)
        let sessionIn = try CoreMLActivityModel.load(modelURL: inURL, computeUnits: .cpuOnly)

        guard let expDouble = vectors["expected_probs_double_normalize_wrong"] as? [[Double]] else {
            XCTFail("missing expected_probs_double_normalize_wrong")
            return
        }

        XCTAssertEqual(raw.count, scaled.count)
        var maxDoubleDiffAll = 0.0
        for i in 0..<raw.count {
            let gotApp = try sessionApp.predict(features: scaled[i])
            let gotIn = try sessionIn.predict(features: raw[i])
            let gotDouble = try sessionApp.predict(features: doubleScaled[i])

            for j in 0..<gotApp.count {
                XCTAssertEqual(gotApp[j], expApp[i][j], accuracy: tol, "app[\(i)][\(j)]")
                XCTAssertEqual(gotIn[j], expIn[i][j], accuracy: tol, "in[\(i)][\(j)]")
                XCTAssertEqual(gotApp[j], gotIn[j], accuracy: tol, "app_vs_in[\(i)][\(j)]")
                XCTAssertEqual(gotDouble[j], expDouble[i][j], accuracy: tol, "double[\(i)][\(j)]")
            }

            let maxDiff = zip(gotDouble, gotApp).map { abs($0 - $1) }.max() ?? 0
            maxDoubleDiffAll = max(maxDoubleDiffAll, maxDiff)
        }
        XCTAssertGreaterThanOrEqual(
            maxDoubleDiffAll,
            minDoubleDiff,
            "double normalize should diverge on at least one vector; maxDiff=\(maxDoubleDiffAll)"
        )
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
        throw NSError(domain: "CoreMLPreprocessInModel", code: 1)
    }
}
#else
final class CoreMLPreprocessInModelParityTests: XCTestCase {
    func testSkipWhenCoreMLUnavailable() throws {
        throw XCTSkip("CoreML unavailable on this platform")
    }
}
#endif
