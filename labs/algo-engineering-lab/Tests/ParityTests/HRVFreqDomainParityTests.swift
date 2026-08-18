import XCTest
@testable import AlgoSwift

// Case3：相对 golden/hrv_freq_domain 逐环快照比对。
// 哪一环先偏，哪一环就是口径问题——不要先怪 FFT。
final class HRVFreqDomainParityTests: XCTestCase {

    private struct GoldenFile: Decodable {
        struct Input: Decodable {
            let rr_ms: [Double]
            let non_finite_mode: String?
        }
        struct Expected: Decodable {
            let lf: Double?
            let hf: Double?
            let lf_hf_ratio: Double?
            let ok: Bool
            let error: String?
        }
        struct Snapshots: Decodable {
            let resampled: [Double]?
            let detrended: [Double]?
            let windowed: [Double]?
            let psd: [Double]?
            let freqs: [Double]?
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
        var checked = 0

        for url in files {
            let data = try Data(contentsOf: url)
            let g = try JSONDecoder().decode(GoldenFile.self, from: data)
            if g.category == "pathological" { pathological += 1 }

            let rr = g.materializeRR()
            if g.expected.ok {
                let got = try HRVFreqDomain.compute(rrMs: rr)

                // —— 中间快照：按链路顺序断言，失败点 = 首个漂移环 ——
                assertVector(got.resampled, g.snapshots.resampled!, abs: 1e-9, id: g.id, ring: "resampled")
                assertVector(got.detrended, g.snapshots.detrended!, abs: 1e-9, id: g.id, ring: "detrended")
                assertVector(got.windowed, g.snapshots.windowed!, abs: 1e-9, id: g.id, ring: "windowed")
                assertVector(got.freqs, g.snapshots.freqs!, abs: 1e-12, id: g.id, ring: "freqs")
                // 朴素 DFT vs numpy.fft：ULP 级差，放宽到 1e-9（相对大功率再放宽）
                assertPSD(got.psd, g.snapshots.psd!, id: g.id)

                // 标量：相对 1% 或绝对 1e-6（取宽松者）
                assertScalarLoose(got.lf, g.expected.lf!, id: g.id, name: "lf")
                assertScalarLoose(got.hf, g.expected.hf!, id: g.id, name: "hf")
                XCTAssertEqual(got.lfHfRatio, g.expected.lf_hf_ratio!, accuracy: 0.01, "\(g.id) lf_hf_ratio")
            } else {
                XCTAssertThrowsError(try HRVFreqDomain.compute(rrMs: rr), g.id) { err in
                    guard let algoErr = err as? AlgoError else {
                        XCTFail("\(g.id) expected AlgoError, got \(err)")
                        return
                    }
                    switch g.expected.error {
                    case "empty": XCTAssertEqual(algoErr, .empty, g.id)
                    case "too_short": XCTAssertEqual(algoErr, .tooShort, g.id)
                    case "non_finite": XCTAssertEqual(algoErr, .nonFinite, g.id)
                    case "invalid_arg": XCTAssertEqual(algoErr, .invalidArgument, g.id)
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

    // MARK: - helpers

    private func assertVector(_ got: [Double], _ exp: [Double], abs: Double, id: String, ring: String) {
        XCTAssertEqual(got.count, exp.count, "\(id) \(ring) length")
        guard got.count == exp.count else { return }
        for i in 0..<got.count {
            XCTAssertEqual(got[i], exp[i], accuracy: abs, "\(id) \(ring)[\(i)]")
        }
    }

    private func assertPSD(_ got: [Double], _ exp: [Double], id: String) {
        XCTAssertEqual(got.count, exp.count, "\(id) psd length")
        guard got.count == exp.count else { return }
        for i in 0..<got.count {
            let tol = max(1e-9, abs(exp[i]) * 1e-12)
            XCTAssertEqual(got[i], exp[i], accuracy: tol, "\(id) psd[\(i)]")
        }
    }

    private func assertScalarLoose(_ got: Double, _ exp: Double, id: String, name: String) {
        let tol = max(1e-6, abs(exp) * 0.01)
        XCTAssertEqual(got, exp, accuracy: tol, "\(id) \(name)")
    }

    private static func goldenDir() throws -> URL {
        var url = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<8 {
            let candidate = url.appendingPathComponent("golden/hrv_freq_domain")
            if FileManager.default.fileExists(atPath: candidate.path) {
                return candidate
            }
            url.deleteLastPathComponent()
        }
        XCTFail("cannot locate golden/hrv_freq_domain from \(#filePath)")
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
