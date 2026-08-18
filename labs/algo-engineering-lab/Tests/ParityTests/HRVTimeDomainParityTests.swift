import XCTest
@testable import AlgoSwift

// Case1：相对 golden/hrv_time_domain 下 JSON 做数值一致性。
// 阈值来自 docs/01（SDNN/RMSSD ≤0.1ms，pNN50 ≤0.5）。
// golden 只能由: uv run python -m python.generate_golden hrv_time_domain
final class HRVTimeDomainParityTests: XCTestCase {

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
        struct Snapshots: Decodable { let mean_rr_ms: Double? }

        let id: String
        let category: String
        let input: Input
        let expected: Expected
        let snapshots: Snapshots

        /// JSON 无法存 NaN/Inf，按 non_finite_mode 在测试侧还原病态输入
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
        var checked = 0

        for url in files {
            let data = try Data(contentsOf: url)
            let g = try JSONDecoder().decode(GoldenFile.self, from: data)
            if g.category == "pathological" { pathological += 1 }

            let rr = g.materializeRR()
            if g.expected.ok {
                let got = try HRVTimeDomain.compute(rrMs: rr)
                XCTAssertEqual(got.sdnnMs, g.expected.sdnn_ms!, accuracy: 0.1, "\(g.id) sdnn")
                XCTAssertEqual(got.rmssdMs, g.expected.rmssd_ms!, accuracy: 0.1, "\(g.id) rmssd")
                XCTAssertEqual(got.pnn50, g.expected.pnn50!, accuracy: 0.5, "\(g.id) pnn50")
                if let mean = g.snapshots.mean_rr_ms {
                    XCTAssertEqual(got.meanRrMs, mean, accuracy: 1e-9, "\(g.id) mean snapshot")
                }
            } else {
                // 错误路径：必须与 golden.error 字段语义一致
                XCTAssertThrowsError(try HRVTimeDomain.compute(rrMs: rr), g.id) { err in
                    guard let algoErr = err as? AlgoError else {
                        XCTFail("\(g.id) expected AlgoError, got \(err)")
                        return
                    }
                    switch g.expected.error {
                    case "empty": XCTAssertEqual(algoErr, .empty, g.id)
                    case "too_short": XCTAssertEqual(algoErr, .tooShort, g.id)
                    case "non_finite": XCTAssertEqual(algoErr, .nonFinite, g.id)
                    default: XCTFail("\(g.id) unknown error key \(String(describing: g.expected.error))")
                    }
                }
            }
            checked += 1
        }

        let ratio = Double(pathological) / Double(files.count)
        XCTAssertGreaterThanOrEqual(ratio, 0.40, "pathological ratio must be >= 40%")
        XCTAssertEqual(checked, files.count)
    }

    func testManualKnownVector() throws {
        // 手工可验算：mean=800；diffs=+20,-40；RMSSD=sqrt(1000)；pNN50=0
        let rr = [800.0, 820.0, 780.0]
        let got = try HRVTimeDomain.compute(rrMs: rr)
        XCTAssertEqual(got.meanRrMs, 800.0, accuracy: 1e-12)
        XCTAssertEqual(got.rmssdMs, sqrt(1000.0), accuracy: 1e-12)
        XCTAssertEqual(got.pnn50, 0.0, accuracy: 1e-12)
    }

    // MARK: - helpers

    private static func goldenDir() throws -> URL {
        // swift test 的 cwd 常在 .build 下，故从源文件位置向上找仓库根
        var url = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<8 {
            let candidate = url.appendingPathComponent("golden/hrv_time_domain")
            if FileManager.default.fileExists(atPath: candidate.path) {
                return candidate
            }
            url.deleteLastPathComponent()
        }
        XCTFail("cannot locate golden/hrv_time_domain from \(#filePath)")
        throw AlgoError.invalidArgument
    }

    private static func loadGoldenFiles() throws -> [URL] {
        let dir = try goldenDir()
        return try FileManager.default.contentsOfDirectory(
            at: dir,
            includingPropertiesForKeys: nil
        )
        .filter { $0.pathExtension == "json" }
        .sorted { $0.lastPathComponent < $1.lastPathComponent }
    }
}
