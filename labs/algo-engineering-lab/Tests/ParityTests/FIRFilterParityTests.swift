import XCTest
@testable import AlgoSwift

// Case2：naive C 与 vDSP 都对照 golden/fir_ppg
final class FIRFilterParityTests: XCTestCase {

    private struct GoldenFile: Decodable {
        struct Input: Decodable {
            let x: [Double]
            let non_finite_mode: String?
        }
        struct Expected: Decodable {
            let y: [Double]?
            let ok: Bool
            let error: String?
        }

        let id: String
        let category: String
        let input: Input
        let expected: Expected

        func materializeX() -> [Double] {
            var x = input.x
            switch input.non_finite_mode {
            case "nan_at_1":
                if x.count > 1 { x[1] = .nan }
            case "inf_at_1":
                if x.count > 1 { x[1] = .infinity }
            default: break
            }
            return x
        }
    }

    private struct CoeffsFile: Decodable {
        let coeffs: [Double]
        let truncation_demo: TruncationDemo?
        struct TruncationDemo: Decodable {
            let max_abs_error_on_1hz_sine: Double
        }
    }

    func testCoeffsMatchGeneratedHeader() throws {
        // Swift 读到的 C 头文件系数，须与 golden/coeffs.json 一致
        let url = try Self.goldenDir().appendingPathComponent("coeffs.json")
        let data = try Data(contentsOf: url)
        let file = try JSONDecoder().decode(CoeffsFile.self, from: data)
        let fromC = FIRCoeffs.bandpass
        XCTAssertEqual(fromC.count, file.coeffs.count)
        for i in 0..<fromC.count {
            XCTAssertEqual(fromC[i], file.coeffs[i], accuracy: 1e-15, "coeff[\(i)]")
        }
        // 截断演示：生成阶段应观察到明显误差（面试讲「6 位有效数字」用）
        if let demo = file.truncation_demo {
            XCTAssertGreaterThan(demo.max_abs_error_on_1hz_sine, 1e-4)
        }
    }

    func testNaiveAndVDSPMatchGolden() throws {
        let files = try Self.loadCaseFiles()
        XCTAssertGreaterThanOrEqual(files.count, 50)

        var pathological = 0
        for url in files {
            let g = try JSONDecoder().decode(GoldenFile.self, from: Data(contentsOf: url))
            if g.category == "pathological" { pathological += 1 }
            let x = g.materializeX()

            if g.expected.ok {
                let expected = g.expected.y!
                let naive = try FIRFilter.filterNaive(x: x)
                let vdsp = try FIRFilter.filterVDSP(x: x)
                XCTAssertEqual(naive.count, expected.count, g.id)
                for i in 0..<expected.count {
                    XCTAssertEqual(naive[i], expected[i], accuracy: 1e-4, "\(g.id) naive[\(i)]")
                    XCTAssertEqual(vdsp[i], expected[i], accuracy: 1e-4, "\(g.id) vdsp[\(i)]")
                }
            } else {
                XCTAssertThrowsError(try FIRFilter.filterNaive(x: x), g.id) { err in
                    self.assertError(err, matches: g.expected.error, id: g.id)
                }
                XCTAssertThrowsError(try FIRFilter.filterVDSP(x: x), g.id) { err in
                    self.assertError(err, matches: g.expected.error, id: g.id)
                }
            }
        }

        let ratio = Double(pathological) / Double(files.count)
        XCTAssertGreaterThanOrEqual(ratio, 0.40)
    }

    private func assertError(_ err: Error, matches key: String?, id: String) {
        guard let algo = err as? AlgoError else {
            XCTFail("\(id) expected AlgoError")
            return
        }
        switch key {
        case "empty": XCTAssertEqual(algo, .empty, id)
        case "non_finite": XCTAssertEqual(algo, .nonFinite, id)
        default: XCTFail("\(id) unexpected \(String(describing: key))")
        }
    }

    private static func goldenDir() throws -> URL {
        var url = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<8 {
            let candidate = url.appendingPathComponent("golden/fir_ppg")
            if FileManager.default.fileExists(atPath: candidate.path) {
                return candidate
            }
            url.deleteLastPathComponent()
        }
        throw AlgoError.invalidArgument
    }

    private static func loadCaseFiles() throws -> [URL] {
        try FileManager.default.contentsOfDirectory(
            at: try goldenDir(),
            includingPropertiesForKeys: nil
        )
        .filter { $0.pathExtension == "json" && $0.lastPathComponent != "coeffs.json" }
        .sorted { $0.lastPathComponent < $1.lastPathComponent }
    }
}
