import XCTest
@testable import AlgoSwift

// Case6：HRV 伪差校正 parity（raw -> mask -> corrected -> metrics）。
final class HRVArtifactCorrectionParityTests: XCTestCase {

    private struct GoldenFile: Decodable {
        struct Input: Decodable {
            let rr_ms: [Double]
            let non_finite_mode: String?
        }
        struct Expected: Decodable {
            let sdnn_ms: Double?
            let rmssd_ms: Double?
            let pnn50: Double?
            let ok: Bool
            let error: String?
        }
        struct Snapshots: Decodable {
            let rr_raw: [Double]?
            let artifact_mask: [UInt8]?
            let rr_corrected: [Double]?
            let mean_rr_ms: Double?
        }
        let id: String
        let category: String
        let input: Input
        let expected: Expected
        let snapshots: Snapshots

        func materializeRR() -> [Double] {
            var rr = input.rr_ms
            switch input.non_finite_mode {
            case "nan_at_1":
                if rr.count > 1 { rr[1] = .nan }
            case "inf_at_1":
                if rr.count > 1 { rr[1] = .infinity }
            default:
                break
            }
            return rr
        }
    }

    func testParityAgainstGoldenDataset() throws {
        let files = try Self.loadGoldenFiles()
        XCTAssertGreaterThanOrEqual(files.count, 50, "golden set too small")

        var pathological = 0
        for url in files {
            let data = try Data(contentsOf: url)
            let g = try JSONDecoder().decode(GoldenFile.self, from: data)
            if g.category == "pathological" { pathological += 1 }

            let rr = g.materializeRR()
            if g.expected.ok {
                let got = try HRVArtifactCorrection.correct(rrMs: rr)
                XCTAssertEqual(got.rrCorrected.count, g.snapshots.rr_corrected!.count, "\(g.id) corrected count")
                XCTAssertEqual(got.artifactMask, g.snapshots.artifact_mask!, "\(g.id) mask")
                for i in 0..<got.rrCorrected.count {
                    XCTAssertEqual(got.rrCorrected[i], g.snapshots.rr_corrected![i], accuracy: 1e-9, "\(g.id) corrected[\(i)]")
                }
                XCTAssertEqual(got.metrics.sdnnMs, g.expected.sdnn_ms!, accuracy: 0.1, "\(g.id) sdnn")
                XCTAssertEqual(got.metrics.rmssdMs, g.expected.rmssd_ms!, accuracy: 0.1, "\(g.id) rmssd")
                XCTAssertEqual(got.metrics.pnn50, g.expected.pnn50!, accuracy: 0.5, "\(g.id) pnn50")
                if let mean = g.snapshots.mean_rr_ms {
                    XCTAssertEqual(got.metrics.meanRrMs, mean, accuracy: 1e-9, "\(g.id) mean")
                }
            } else {
                XCTAssertThrowsError(try HRVArtifactCorrection.correct(rrMs: rr), g.id) { err in
                    guard let algoErr = err as? AlgoError else {
                        XCTFail("\(g.id) expected AlgoError, got \(err)")
                        return
                    }
                    switch g.expected.error {
                    case "empty": XCTAssertEqual(algoErr, .empty, g.id)
                    case "too_short": XCTAssertEqual(algoErr, .tooShort, g.id)
                    case "non_finite": XCTAssertEqual(algoErr, .nonFinite, g.id)
                    default: XCTFail("\(g.id) unknown error \(String(describing: g.expected.error))")
                    }
                }
            }
        }

        let ratio = Double(pathological) / Double(files.count)
        XCTAssertGreaterThanOrEqual(ratio, 0.40, "pathological ratio must be >= 40%")
    }

    private static func goldenDir() throws -> URL {
        var url = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<8 {
            let candidate = url.appendingPathComponent("golden/hrv_artifact_correction")
            if FileManager.default.fileExists(atPath: candidate.path) {
                return candidate
            }
            url.deleteLastPathComponent()
        }
        XCTFail("cannot locate golden/hrv_artifact_correction from \(#filePath)")
        throw AlgoError.invalidArgument
    }

    private static func loadGoldenFiles() throws -> [URL] {
        let dir = try goldenDir()
        return try FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil)
            .filter { $0.pathExtension == "json" }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
    }
}
