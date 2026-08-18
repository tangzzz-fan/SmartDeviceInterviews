import XCTest
@testable import AlgoSwift

#if canImport(CoreML)
import CoreML

final class CoreMLStreamingParityTests: XCTestCase {
    func testStreamingPipelineMatchesGolden() throws {
        let reportURL = try Self.locate("golden/coreml_streaming/stream_report.json")
        let data = try Data(contentsOf: reportURL)
        guard let report = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let input = report["input"] as? [String: Any],
              let packetsJSON = input["packets"] as? [[String: Any]],
              let preprocess = report["preprocess"] as? [String: Any],
              let mean = preprocess["mean"] as? [Double],
              let scale = preprocess["scale"] as? [Double],
              let modelRel = report["model"] as? String,
              let expected = report["expected"] as? [String: Any],
              let expFeats = expected["window_features"] as? [[Double]],
              let expProbs = expected["probs"] as? [[Double]],
              let tolFeat = report["tolerance_features_abs"] as? Double,
              let tolProb = report["tolerance_probs_abs"] as? Double else {
            XCTFail("malformed stream_report.json")
            return
        }

        let session = try CoreMLActivityModel.load(
            modelURL: try Self.locate(modelRel),
            computeUnits: .cpuOnly
        )
        let pipe = CoreMLStreamingPipeline(session: session, mean: mean, scale: scale)

        for p in packetsJSON {
            let seq = (p["seq"] as? Int).map(UInt64.init) ?? UInt64(p["seq"] as? Int64 ?? 0)
            let samples = (p["samples"] as? [Double]) ?? []
            try pipe.ingest(BLEPacket(seq: seq, samples: samples))
        }

        XCTAssertEqual(pipe.featureWindows.count, expFeats.count)
        XCTAssertEqual(pipe.probabilityWindows.count, expProbs.count)
        for i in 0..<expFeats.count {
            XCTAssertEqual(pipe.featureWindows[i].count, expFeats[i].count)
            for j in 0..<expFeats[i].count {
                XCTAssertEqual(
                    pipe.featureWindows[i][j],
                    expFeats[i][j],
                    accuracy: tolFeat,
                    "feat[\(i)][\(j)]"
                )
            }
            for j in 0..<expProbs[i].count {
                XCTAssertEqual(
                    pipe.probabilityWindows[i][j],
                    expProbs[i][j],
                    accuracy: tolProb,
                    "prob[\(i)][\(j)]"
                )
            }
        }
    }

    func testActorMatchesSyncPipeline() async throws {
        let reportURL = try Self.locate("golden/coreml_streaming/stream_report.json")
        let data = try Data(contentsOf: reportURL)
        guard let report = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let input = report["input"] as? [String: Any],
              let packetsJSON = input["packets"] as? [[String: Any]],
              let preprocess = report["preprocess"] as? [String: Any],
              let mean = preprocess["mean"] as? [Double],
              let scale = preprocess["scale"] as? [Double],
              let modelRel = report["model"] as? String,
              let expected = report["expected"] as? [String: Any],
              let expProbs = expected["probs"] as? [[Double]],
              let tolProb = report["tolerance_probs_abs"] as? Double else {
            XCTFail("malformed stream_report.json")
            return
        }

        let session = try CoreMLActivityModel.load(
            modelURL: try Self.locate(modelRel),
            computeUnits: .cpuOnly
        )
        let pipe = CoreMLStreamingPipeline(session: session, mean: mean, scale: scale)
        let actor = CoreMLStreamingInferenceActor(pipeline: pipe)

        for p in packetsJSON {
            let seq = (p["seq"] as? Int).map(UInt64.init) ?? UInt64(p["seq"] as? Int64 ?? 0)
            let samples = (p["samples"] as? [Double]) ?? []
            try await actor.ingest(BLEPacket(seq: seq, samples: samples))
        }
        let probs = await actor.probabilityWindows()
        XCTAssertEqual(probs.count, expProbs.count)
        for i in 0..<expProbs.count {
            for j in 0..<expProbs[i].count {
                XCTAssertEqual(probs[i][j], expProbs[i][j], accuracy: tolProb)
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
        throw NSError(domain: "CoreMLStreaming", code: 1)
    }
}
#else
final class CoreMLStreamingParityTests: XCTestCase {
    func testSkipWhenCoreMLUnavailable() throws {
        throw XCTSkip("CoreML unavailable on this platform")
    }
}
#endif
