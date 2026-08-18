import XCTest
@testable import AlgoSwift

/// Benchmark 目标：只记性能，不断言 golden（见 docs/05）。
final class SmokeBenchmarkTests: XCTestCase {
    func testVersionCallIsCheap() throws {
        // measure 会多次调用；此处仅验证 harness，真实 DSP 基准在后续 case
        measure {
            for _ in 0..<1000 {
                _ = try? AlgoVersion.current()
            }
        }
    }
}
