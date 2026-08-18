import XCTest
@testable import AlgoSwift

#if canImport(CoreML)
import CoreML
#endif

/// T13：统一基准入口（FIR / CoreML / Sleep 后处理）。
/// T14：CoreML 拆分 compile_every_call / 缓存后纯推理 / cpuOnly vs all。
/// 不阻塞 CI，仅输出可复现数字并追加到 bench-log。
final class UnifiedPerfPowerBenchmarkTests: XCTestCase {

    func testUnifiedPerfSnapshot() throws {
        let fir = try benchmarkFIR()
        let coreml = try benchmarkCoreML()
        let sleep = try benchmarkSleepPostprocess()

        print(
            """
            [T13/T14 unified-bench]
            fir_naive_ms p50=\(fmt(fir.naiveP50)) p95=\(fmt(fir.naiveP95))
            fir_vdsp_ms  p50=\(fmt(fir.vdspP50)) p95=\(fmt(fir.vdspP95)) speedup=\(fmt(fir.speedup))x
            coreml_compile_every_call_ms p50=\(fmt(coreml.compileEvery.p50)) p95=\(fmt(coreml.compileEvery.p95))
            coreml_infer_cached_all_ms   p50=\(fmt(coreml.inferAll.p50)) p95=\(fmt(coreml.inferAll.p95))
            coreml_infer_cached_cpu_ms   p50=\(fmt(coreml.inferCPU.p50)) p95=\(fmt(coreml.inferCPU.p95))
            sleep_postprocess_ms p50=\(fmt(sleep.p50)) p95=\(fmt(sleep.p95))
            """
        )
    }

    private func benchmarkFIR() throws -> (naiveP50: Double, naiveP95: Double, vdspP50: Double, vdspP95: Double, speedup: Double) {
        let fs = 25.0
        let n = Int(fs * 8.0)
        let x = (0..<n).map { i in
            let t = Double(i) / fs
            return sin(2 * .pi * 1.2 * t)
        }
        _ = try FIRFilter.filterNaive(x: x)
        _ = try FIRFilter.filterVDSP(x: x)

        var naive: [Double] = []
        var vdsp: [Double] = []
        let rounds = 40
        for _ in 0..<rounds {
            let t0 = CFAbsoluteTimeGetCurrent()
            _ = try FIRFilter.filterNaive(x: x)
            naive.append((CFAbsoluteTimeGetCurrent() - t0) * 1000)

            let t1 = CFAbsoluteTimeGetCurrent()
            _ = try FIRFilter.filterVDSP(x: x)
            vdsp.append((CFAbsoluteTimeGetCurrent() - t1) * 1000)
        }
        let n50 = percentile(naive, 0.50)
        let v50 = percentile(vdsp, 0.50)
        return (n50, percentile(naive, 0.95), v50, percentile(vdsp, 0.95), n50 / max(v50, 1e-9))
    }

    private struct CoreMLBench {
        let compileEvery: (p50: Double, p95: Double)
        let inferAll: (p50: Double, p95: Double)
        let inferCPU: (p50: Double, p95: Double)
    }

    private func benchmarkCoreML() throws -> CoreMLBench {
        #if canImport(CoreML)
        let modelURL = try locate("artifacts/coreml/activity_fp32.mlpackage")
        let x: [Double] = [0.2, -0.1, 0.3, 0.1, 0.0, 0.2, -0.05, 0.12]
        let rounds = 30

        // 对照：旧路径每次 compile + load + predict
        _ = try CoreMLActivityModel.predictProbabilities(modelURL: modelURL, features: x, computeUnits: .all)
        var compileSamples: [Double] = []
        for _ in 0..<rounds {
            let t0 = CFAbsoluteTimeGetCurrent()
            _ = try CoreMLActivityModel.predictProbabilities(modelURL: modelURL, features: x, computeUnits: .all)
            compileSamples.append((CFAbsoluteTimeGetCurrent() - t0) * 1000)
        }

        // 纯推理：.all
        let sessionAll = try CoreMLActivityModel.load(modelURL: modelURL, computeUnits: .all)
        _ = try sessionAll.predict(features: x)
        var inferAllSamples: [Double] = []
        for _ in 0..<rounds {
            let t0 = CFAbsoluteTimeGetCurrent()
            _ = try sessionAll.predict(features: x)
            inferAllSamples.append((CFAbsoluteTimeGetCurrent() - t0) * 1000)
        }

        // 纯推理：.cpuOnly
        let sessionCPU = try CoreMLActivityModel.load(modelURL: modelURL, computeUnits: .cpuOnly)
        _ = try sessionCPU.predict(features: x)
        var inferCPUSamples: [Double] = []
        for _ in 0..<rounds {
            let t0 = CFAbsoluteTimeGetCurrent()
            _ = try sessionCPU.predict(features: x)
            inferCPUSamples.append((CFAbsoluteTimeGetCurrent() - t0) * 1000)
        }

        return CoreMLBench(
            compileEvery: (percentile(compileSamples, 0.50), percentile(compileSamples, 0.95)),
            inferAll: (percentile(inferAllSamples, 0.50), percentile(inferAllSamples, 0.95)),
            inferCPU: (percentile(inferCPUSamples, 0.50), percentile(inferCPUSamples, 0.95))
        )
        #else
        return CoreMLBench(compileEvery: (0, 0), inferAll: (0, 0), inferCPU: (0, 0))
        #endif
    }

    private func benchmarkSleepPostprocess() throws -> (p50: Double, p95: Double) {
        let prob = [0.80, 0.05, 0.05, 0.05, 0.05]
        let seq = Array(repeating: prob, count: 120)
        _ = try SleepStagingPostprocess.run(probSeq: seq)
        var samples: [Double] = []
        for _ in 0..<40 {
            let t0 = CFAbsoluteTimeGetCurrent()
            _ = try SleepStagingPostprocess.run(probSeq: seq)
            samples.append((CFAbsoluteTimeGetCurrent() - t0) * 1000)
        }
        return (percentile(samples, 0.50), percentile(samples, 0.95))
    }

    private func percentile(_ values: [Double], _ p: Double) -> Double {
        let s = values.sorted()
        let idx = min(s.count - 1, Int(Double(s.count - 1) * p))
        return s[idx]
    }

    private func fmt(_ x: Double) -> String {
        String(format: "%.4f", x)
    }

    private func locate(_ relative: String) throws -> URL {
        var url = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
        for _ in 0..<8 {
            let candidate = url.appendingPathComponent(relative)
            if FileManager.default.fileExists(atPath: candidate.path) {
                return candidate
            }
            url.deleteLastPathComponent()
        }
        throw NSError(domain: "UnifiedPerfBenchmark", code: 1)
    }
}
