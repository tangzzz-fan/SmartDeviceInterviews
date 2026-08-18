import XCTest
import Foundation

final class CoreMLDriftMonitoringParityTests: XCTestCase {
    private struct Report: Decodable {
        struct Thresholds: Decodable {
            let psi_medium: Double
            let psi_high: Double
            let kl_medium: Double
            let kl_high: Double
        }
        struct Section: Decodable {
            let feature_psi: [Double]
            let max_psi: Double
            let kl_confidence: Double
            let alert_level: String
        }
        struct Pass: Decodable {
            let stable_low_alert: Bool
            let shifted_not_low: Bool
            let shifted_more_than_stable: Bool
        }
        let caseName: String
        let thresholds: Thresholds
        let stable: Section
        let shifted: Section
        let pass: Pass
        let disclaimer: String

        enum CodingKeys: String, CodingKey {
            case caseName = "case"
            case thresholds, stable, shifted, pass, disclaimer
        }
    }

    func testDriftReportSemantics() throws {
        let data = try Data(contentsOf: Self.reportURL())
        let report = try JSONDecoder().decode(Report.self, from: data)
        XCTAssertEqual(report.caseName, "coreml_drift_monitoring")
        XCTAssertTrue(report.disclaimer.contains("验证性原型"))

        XCTAssertTrue(report.pass.stable_low_alert)
        XCTAssertTrue(report.pass.shifted_not_low)
        XCTAssertTrue(report.pass.shifted_more_than_stable)

        XCTAssertLessThan(report.stable.max_psi, report.thresholds.psi_medium)
        XCTAssertLessThan(report.stable.kl_confidence, report.thresholds.kl_medium)
        XCTAssertGreaterThanOrEqual(report.shifted.max_psi, report.thresholds.psi_medium)
    }

    private static func reportURL() throws -> URL {
        var url = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<8 {
            let candidate = url.appendingPathComponent("golden/coreml_drift_monitoring/report.json")
            if FileManager.default.fileExists(atPath: candidate.path) {
                return candidate
            }
            url.deleteLastPathComponent()
        }
        XCTFail("cannot locate golden/coreml_drift_monitoring/report.json")
        throw NSError(domain: "CoreMLDriftMonitoring", code: 1)
    }
}
