import Foundation

public enum SleepStage: String, CaseIterable {
    case w = "W"
    case n1 = "N1"
    case n2 = "N2"
    case n3 = "N3"
    case rem = "REM"
}

public struct SleepStagingResult: Equatable {
    public var rawStages: [String]
    public var smoothedStages: [String]
    public var totalEpochs: Int
    public var sleepEpochs: Int
    public var tstMin: Double
    public var solMin: Double
}

public enum SleepStagingPostprocess {
    private static func argmaxStage(_ probs: [Double]) throws -> String {
        guard probs.count == 5 else { throw AlgoError.invalidArgument }
        guard let maxIndex = probs.enumerated().max(by: { $0.element < $1.element })?.offset else {
            throw AlgoError.invalidArgument
        }
        return SleepStage.allCases[maxIndex].rawValue
    }

    private static func majority3(_ stages: [String]) -> [String] {
        guard stages.count >= 3 else { return stages }
        var out = stages
        for i in 1..<(stages.count - 1) {
            let left = stages[i - 1]
            let mid = stages[i]
            let right = stages[i + 1]
            if left == mid || left == right {
                out[i] = left
            } else if mid == right {
                out[i] = mid
            } else {
                // 三者全不同时，按 Python Counter.most_common 的稳定行为取窗口首元素
                out[i] = left
            }
        }
        return out
    }

    private static func collapseSingletons(_ stages: [String]) -> [String] {
        guard stages.count >= 3 else { return stages }
        var out = stages
        for i in 1..<(stages.count - 1) {
            if out[i - 1] == out[i + 1], out[i] != out[i - 1] {
                out[i] = out[i - 1]
            }
        }
        return out
    }

    private static func metrics(for stages: [String]) -> (Int, Int, Double, Double) {
        let total = stages.count
        let sleep = stages.filter { $0 != SleepStage.w.rawValue }.count
        let tst = Double(sleep) * 0.5
        let solEpoch = stages.firstIndex(where: { $0 != SleepStage.w.rawValue }) ?? total
        let sol = Double(solEpoch) * 0.5
        return (total, sleep, tst, sol)
    }

    /**
     每 30s 概率序列 -> 平滑分期序列 + 指标。
     */
    public static func run(probSeq: [[Double]]) throws -> SleepStagingResult {
        let raw = try probSeq.map { try argmaxStage($0) }
        let s1 = majority3(raw)
        let smoothed = collapseSingletons(s1)
        let (total, sleep, tst, sol) = metrics(for: smoothed)
        return SleepStagingResult(
            rawStages: raw,
            smoothedStages: smoothed,
            totalEpochs: total,
            sleepEpochs: sleep,
            tstMin: tst,
            solMin: sol
        )
    }
}
