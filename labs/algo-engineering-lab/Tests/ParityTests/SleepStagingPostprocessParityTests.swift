import XCTest
@testable import AlgoSwift

final class SleepStagingPostprocessParityTests: XCTestCase {
    private struct GoldenFile: Decodable {
        struct Input: Decodable {
            let epoch_sec: Int
            let prob_seq: [[Double]]
        }
        struct Expected: Decodable {
            struct Metrics: Decodable {
                let total_epochs: Int
                let sleep_epochs: Int
                let tst_min: Double
                let sol_min: Double
            }
            let raw_stages: [String]
            let smoothed_stages: [String]
            let metrics: Metrics
            let ok: Bool
        }
        let id: String
        let input: Input
        let expected: Expected
    }

    func testParityAgainstGoldenDataset() throws {
        let files = try Self.loadGoldenFiles()
        XCTAssertGreaterThanOrEqual(files.count, 30)
        for url in files {
            let data = try Data(contentsOf: url)
            let g = try JSONDecoder().decode(GoldenFile.self, from: data)
            let got = try SleepStagingPostprocess.run(probSeq: g.input.prob_seq)
            XCTAssertEqual(got.rawStages, g.expected.raw_stages, "\(g.id) raw")
            XCTAssertEqual(got.smoothedStages, g.expected.smoothed_stages, "\(g.id) smoothed")
            XCTAssertEqual(got.totalEpochs, g.expected.metrics.total_epochs, "\(g.id) total")
            XCTAssertEqual(got.sleepEpochs, g.expected.metrics.sleep_epochs, "\(g.id) sleep")
            XCTAssertEqual(got.tstMin, g.expected.metrics.tst_min, accuracy: 1e-9, "\(g.id) tst")
            XCTAssertEqual(got.solMin, g.expected.metrics.sol_min, accuracy: 1e-9, "\(g.id) sol")
        }
    }

    private static func goldenDir() throws -> URL {
        var url = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<8 {
            let candidate = url.appendingPathComponent("golden/sleep_staging_postprocess")
            if FileManager.default.fileExists(atPath: candidate.path) {
                return candidate
            }
            url.deleteLastPathComponent()
        }
        XCTFail("cannot locate golden/sleep_staging_postprocess")
        throw NSError(domain: "SleepStagingPostprocess", code: 1)
    }

    private static func loadGoldenFiles() throws -> [URL] {
        let dir = try goldenDir()
        return try FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil)
            .filter { $0.pathExtension == "json" }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
    }
}
