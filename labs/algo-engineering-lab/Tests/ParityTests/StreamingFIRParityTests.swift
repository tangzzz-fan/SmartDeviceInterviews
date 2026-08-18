import XCTest
@testable import AlgoSwift

// Case5：流式因果 FIR + RingBuffer + 丢包 zero_fill。
// 口径：docs/02-算法对齐口径/streaming-fir.md
final class StreamingFIRParityTests: XCTestCase {

    private struct GoldenFile: Decodable {
        struct Packet: Decodable {
            let seq: UInt64
            let samples: [Double]
        }
        struct Input: Decodable {
            let packet_size: Int
            let window: Int
            let gap_policy: String
            let packets: [Packet]
            let drop_seqs: [Int]?
        }
        struct Expected: Decodable {
            let y: [Double]
            let ok: Bool
        }

        let id: String
        let category: String
        let input: Input
        let expected: Expected
    }

    func testContinuousStreamingMatchesCausalGolden() throws {
        let g = try Self.load("stream_001_continuous.json")
        let pipe = StreamingFIRPipeline(
            ringCapacity: 64,
            windowSize: g.input.window,
            gapPolicy: .zeroFill,
            samplesPerMissingPacket: g.input.packet_size
        )
        for p in g.input.packets {
            try pipe.ingest(BLEPacket(seq: p.seq, samples: p.samples))
        }
        let got = pipe.flatOutput
        XCTAssertEqual(got.count, g.expected.y.count, g.id)
        for i in 0..<got.count {
            XCTAssertEqual(got[i], g.expected.y[i], accuracy: 1e-12, "\(g.id)[\(i)]")
        }
    }

    func testPacketLossZeroFillMatchesGolden() throws {
        let g = try Self.load("stream_002_drop_zero_fill.json")
        let pipe = StreamingFIRPipeline(
            ringCapacity: 128,
            windowSize: g.input.window,
            gapPolicy: .zeroFill,
            samplesPerMissingPacket: g.input.packet_size
        )
        for p in g.input.packets {
            try pipe.ingest(BLEPacket(seq: p.seq, samples: p.samples))
        }
        XCTAssertGreaterThan(pipe.gapEvents, 0, "should detect drops")
        let got = pipe.flatOutput
        XCTAssertEqual(got.count, g.expected.y.count, g.id)
        for i in 0..<got.count {
            XCTAssertEqual(got[i], g.expected.y[i], accuracy: 1e-12, "\(g.id)[\(i)]")
        }
    }

    func testResetEachWindowBreaksContinuity() throws {
        // 负例：每窗 reset → 与连续状态 golden 在边界后明显偏离
        let g = try Self.load("stream_001_continuous.json")
        let bad = StreamingFIRPipeline(
            ringCapacity: 64,
            windowSize: g.input.window,
            resetStateEachWindow: true
        )
        for p in g.input.packets {
            try bad.ingest(BLEPacket(seq: p.seq, samples: p.samples))
        }
        let got = bad.flatOutput
        XCTAssertEqual(got.count, g.expected.y.count)
        var maxAbs = 0.0
        for i in 0..<got.count {
            maxAbs = max(maxAbs, abs(got[i] - g.expected.y[i]))
        }
        XCTAssertGreaterThan(maxAbs, 1e-6, "reset-each-window should create boundary artifacts")
        XCTAssertEqual(bad.outputs.count, got.count / g.input.window)
    }

    func testEmptyPacketsProduceNoOutput() throws {
        let g = try Self.load("stream_003_empty.json")
        let pipe = StreamingFIRPipeline(windowSize: g.input.window)
        XCTAssertTrue(pipe.flatOutput.isEmpty)
        XCTAssertEqual(g.expected.y.count, 0)
    }

    // MARK: - helpers

    private static func load(_ name: String) throws -> GoldenFile {
        var url = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<8 {
            let candidate = url.appendingPathComponent("golden/streaming_fir/\(name)")
            if FileManager.default.fileExists(atPath: candidate.path) {
                let data = try Data(contentsOf: candidate)
                return try JSONDecoder().decode(GoldenFile.self, from: data)
            }
            url.deleteLastPathComponent()
        }
        XCTFail("missing golden \(name)")
        throw AlgoError.invalidArgument
    }
}
