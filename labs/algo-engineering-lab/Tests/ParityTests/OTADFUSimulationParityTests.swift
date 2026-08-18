import XCTest
@testable import AlgoSwift

final class OTADFUSimulationParityTests: XCTestCase {
    private struct GoldenFile: Decodable {
        struct Input: Decodable {
            let events: [String]
            let target_chunks: Int
        }
        struct Expected: Decodable {
            struct Funnel: Decodable {
                let started: Int
                let transfer_completed: Int
                let verified: Int
                let activated: Int
            }
            let final_state: String
            let funnel: Funnel
            let progress_chunks: Int
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
            let got = OTADFUSimulator.simulate(events: g.input.events, targetChunks: g.input.target_chunks)
            XCTAssertEqual(got.finalState, g.expected.final_state, "\(g.id) final_state")
            XCTAssertEqual(got.progressChunks, g.expected.progress_chunks, "\(g.id) progress")
            XCTAssertEqual(got.started, g.expected.funnel.started, "\(g.id) started")
            XCTAssertEqual(got.transferCompleted, g.expected.funnel.transfer_completed, "\(g.id) transfer_completed")
            XCTAssertEqual(got.verified, g.expected.funnel.verified, "\(g.id) verified")
            XCTAssertEqual(got.activated, g.expected.funnel.activated, "\(g.id) activated")
        }
    }

    private static func goldenDir() throws -> URL {
        var url = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<8 {
            let candidate = url.appendingPathComponent("golden/ota_dfu_state_machine")
            if FileManager.default.fileExists(atPath: candidate.path) {
                return candidate
            }
            url.deleteLastPathComponent()
        }
        XCTFail("cannot locate golden/ota_dfu_state_machine")
        throw NSError(domain: "OTADFU", code: 1)
    }

    private static func loadGoldenFiles() throws -> [URL] {
        let dir = try goldenDir()
        return try FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil)
            .filter { $0.pathExtension == "json" }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
    }
}
