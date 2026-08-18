import XCTest
@testable import AlgoSwift

final class MultiChannelSyncParityTests: XCTestCase {
    private struct GoldenFile: Decodable {
        struct Input: Decodable {
            struct Packet: Decodable {
                let seq: Int
                let channel_id: String
                let sample_count: Int
                let t0: Double
                let dt: Double
                let samples: [Double]
            }
            let channels: [String]
            let dt_ref: Double
            let zero_fill: Bool
            let packets: [Packet]
        }
        struct Expected: Decodable {
            let timeline: [Double]
            let aligned: [String: [Double]]
            let mask: [String: [Int]]
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

            let packets = g.input.packets.map {
                MultiChannelPacket(
                    seq: $0.seq,
                    channelID: $0.channel_id,
                    sampleCount: $0.sample_count,
                    t0: $0.t0,
                    dt: $0.dt,
                    samples: $0.samples
                )
            }
            let got = try MultiChannelSync.rebuildTimeline(
                packets: packets,
                channels: g.input.channels,
                dtRef: g.input.dt_ref,
                zeroFill: g.input.zero_fill
            )

            XCTAssertEqual(got.timeline.count, g.expected.timeline.count, "\(g.id) timeline count")
            for i in 0..<got.timeline.count {
                XCTAssertEqual(got.timeline[i], g.expected.timeline[i], accuracy: 1e-12, "\(g.id) timeline[\(i)]")
            }
            for ch in g.input.channels {
                let ga = got.aligned[ch] ?? []
                let ea = g.expected.aligned[ch] ?? []
                XCTAssertEqual(ga.count, ea.count, "\(g.id) \(ch) aligned count")
                for i in 0..<ga.count {
                    XCTAssertEqual(ga[i], ea[i], accuracy: 1e-9, "\(g.id) \(ch) aligned[\(i)]")
                }
                XCTAssertEqual(got.mask[ch] ?? [], g.expected.mask[ch] ?? [], "\(g.id) \(ch) mask")
            }
        }
    }

    private static func goldenDir() throws -> URL {
        var url = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<8 {
            let candidate = url.appendingPathComponent("golden/multi_channel_sync")
            if FileManager.default.fileExists(atPath: candidate.path) {
                return candidate
            }
            url.deleteLastPathComponent()
        }
        XCTFail("cannot locate golden/multi_channel_sync")
        throw NSError(domain: "MultiChannelSync", code: 1)
    }

    private static func loadGoldenFiles() throws -> [URL] {
        let dir = try goldenDir()
        return try FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil)
            .filter { $0.pathExtension == "json" }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
    }
}
