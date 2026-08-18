import XCTest
@testable import AlgoSwift

/// Parity 目标：只做精度/契约断言，不写性能（性能在 BenchmarkTests）。
final class SmokeParityTests: XCTestCase {
    func testAlgoVersionReadable() throws {
        // 若链接错库或头文件不同步，这里会先失败
        let v = try AlgoVersion.current()
        XCTAssertEqual(v.major, 0)
        XCTAssertEqual(v.minor, 1)
        XCTAssertEqual(v.patch, 0)
    }
}
