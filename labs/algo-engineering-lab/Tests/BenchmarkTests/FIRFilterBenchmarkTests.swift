import XCTest
@testable import AlgoSwift

/// Case2 性能：naive C vs vDSP。数字必须带环境五项（见 docs/05 / bench-log）。
final class FIRFilterBenchmarkTests: XCTestCase {

    func testNaiveVersusVDSPThroughput() throws {
        // 合成约 8 秒 @25Hz；对比 naive C 整段卷积 vs Accelerate 路径
        let fs = 25.0
        let seconds = 8.0
        let n = Int(fs * seconds)
        var x = [Double](repeating: 0, count: n)
        for i in 0..<n {
            let t = Double(i) / fs
            x[i] = sin(2 * .pi * 1.2 * t)
        }

        // 预热，避免把首次缓存冷启动算进对比
        _ = try FIRFilter.filterNaive(x: x)
        _ = try FIRFilter.filterVDSP(x: x)

        var naiveSamples: [TimeInterval] = []
        var vdspSamples: [TimeInterval] = []
        let rounds = 40

        for _ in 0..<rounds {
            let t0 = CFAbsoluteTimeGetCurrent()
            _ = try FIRFilter.filterNaive(x: x)
            naiveSamples.append(CFAbsoluteTimeGetCurrent() - t0)

            let t1 = CFAbsoluteTimeGetCurrent()
            _ = try FIRFilter.filterVDSP(x: x)
            vdspSamples.append(CFAbsoluteTimeGetCurrent() - t1)
        }

        func percentile(_ values: [TimeInterval], _ p: Double) -> TimeInterval {
            let s = values.sorted()
            let idx = min(s.count - 1, Int(Double(s.count - 1) * p))
            return s[idx]
        }

        let naiveP50 = percentile(naiveSamples, 0.50) * 1000
        let naiveP95 = percentile(naiveSamples, 0.95) * 1000
        let vdspP50 = percentile(vdspSamples, 0.50) * 1000
        let vdspP95 = percentile(vdspSamples, 0.95) * 1000
        let speedup = naiveP50 / max(vdspP50, 1e-9)

        // 打印到测试日志，便于抄进 docs/bench-log.md（面试数字必须可复现）
        print("""
        [FIR bench]
        n=\(n) rounds=\(rounds)
        naive_ms p50=\(String(format: "%.4f", naiveP50)) p95=\(String(format: "%.4f", naiveP95))
        vdsp_ms  p50=\(String(format: "%.4f", vdspP50)) p95=\(String(format: "%.4f", vdspP95))
        speedup(p50)=\(String(format: "%.2f", speedup))x
        """)

        // 不把加速比写死断言（机型差异大）；只要求两边都能跑完且结果有限
        XCTAssertGreaterThan(naiveP50, 0)
        XCTAssertGreaterThan(vdspP50, 0)
        XCTAssertTrue(speedup.isFinite)
    }
}
