import XCTest
import Foundation

/// Case4：断言可复现的量化对比报告阈值（报告由 Python/coremltools 生成）。
/// 本测试不在 CI 里重训模型——重训入口：
/// `uv sync --extra ml && uv run python -m python.generate_golden coreml_quant`
final class CoreMLQuantParityTests: XCTestCase {

    private struct Report: Decodable {
        struct Metrics: Decodable {
            let top1_agreement_fp16_vs_fp32: Double
            let confidence_shift_mean: Double
            let confidence_shift_std: Double
        }
        struct Thresholds: Decodable {
            let top1_agreement_min: Double
            let confidence_shift_mean_abs_max: Double
        }
        struct Pass: Decodable {
            let top1: Bool
            let conf_shift: Bool
        }

        let caseName: String
        let disclaimer: String
        let metrics: Metrics
        let thresholds: Thresholds
        let pass: Pass

        enum CodingKeys: String, CodingKey {
            case caseName = "case"
            case disclaimer, metrics, thresholds, pass
        }
    }

    func testCompareReportMeetsLabThresholds() throws {
        let url = try Self.reportURL()
        let data = try Data(contentsOf: url)
        let report = try JSONDecoder().decode(Report.self, from: data)

        XCTAssertEqual(report.caseName, "coreml_quant")
        XCTAssertTrue(report.disclaimer.contains("验证性原型"), "must stay non-production wording")

        XCTAssertGreaterThanOrEqual(
            report.metrics.top1_agreement_fp16_vs_fp32,
            report.thresholds.top1_agreement_min,
            "FP16 vs FP32 top-1 agreement"
        )
        XCTAssertLessThanOrEqual(
            abs(report.metrics.confidence_shift_mean),
            report.thresholds.confidence_shift_mean_abs_max,
            "confidence shift mean"
        )
        XCTAssertTrue(report.pass.top1 && report.pass.conf_shift)
    }

    private static func reportURL() throws -> URL {
        var url = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<8 {
            let candidate = url.appendingPathComponent("golden/coreml_quant/compare_report.json")
            if FileManager.default.fileExists(atPath: candidate.path) {
                return candidate
            }
            url.deleteLastPathComponent()
        }
        XCTFail("cannot locate golden/coreml_quant/compare_report.json")
        throw NSError(domain: "CoreMLQuant", code: 1)
    }
}
