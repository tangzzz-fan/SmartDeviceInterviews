import Foundation
import AlgoC

/// 将 C 层 `ALGO_ERR_*` 翻译成 Swift 可 `throw` 的错误（见 docs/04）。
public enum AlgoError: Error, Equatable {
    case empty
    case tooShort
    case nonFinite
    case nullPointer
    case invalidArgument
    case unknown(code: Int32)

    public init(algoCode code: Int32) {
        switch code {
        case Int32(ALGO_OK):
            preconditionFailure("ALGO_OK is not an error")
        case Int32(ALGO_ERR_EMPTY): self = .empty
        case Int32(ALGO_ERR_TOO_SHORT): self = .tooShort
        case Int32(ALGO_ERR_NON_FINITE): self = .nonFinite
        case Int32(ALGO_ERR_NULL_POINTER): self = .nullPointer
        case Int32(ALGO_ERR_INVALID_ARG): self = .invalidArgument
        default: self = .unknown(code: code)
        }
    }
}

public enum AlgoVersion {
    /// 读取 AlgoC 编译进进程的版本（冒烟：确认链接正确）。
    public static func current() throws -> (major: Int32, minor: Int32, patch: Int32) {
        var major: Int32 = 0
        var minor: Int32 = 0
        var patch: Int32 = 0
        let code = algo_version(&major, &minor, &patch)
        guard code == ALGO_OK else { throw AlgoError(algoCode: code) }
        return (major, minor, patch)
    }
}

/// HRV 时域结果（ms / 百分点），与 golden `expected` 字段对齐。
public struct HRVTimeDomainResult: Equatable {
    public var sdnnMs: Double
    public var rmssdMs: Double
    public var pnn50: Double
    public var meanRrMs: Double
}

public enum HRVTimeDomain {
    /**
     计算 SDNN / RMSSD / pNN50。

     - Important: 使用连续 `Double` 缓冲零拷贝传给 C（docs/04），
       不要在热路径上逐元素装箱。
     - Note: 单位必须是 **毫秒**；本 case 不做伪差校正。
     */
    public static func compute(rrMs: [Double]) throws -> HRVTimeDomainResult {
        // 空数组：走 C 的 EMPTY，保持跨语言错误语义一致
        if rrMs.isEmpty {
            throw AlgoError.empty
        }

        var sdnn = 0.0
        var rmssd = 0.0
        var pnn50 = 0.0
        var mean = 0.0

        // withUnsafeBufferPointer：把 Swift Array 的连续存储直接交给 C
        let code: Int32 = rrMs.withUnsafeBufferPointer { buf in
            guard let base = buf.baseAddress else {
                return Int32(ALGO_ERR_NULL_POINTER)
            }
            return algo_hrv_time_domain(
                base,
                buf.count,
                &sdnn,
                &rmssd,
                &pnn50,
                &mean
            )
        }

        guard code == ALGO_OK else { throw AlgoError(algoCode: code) }
        return HRVTimeDomainResult(
            sdnnMs: sdnn,
            rmssdMs: rmssd,
            pnn50: pnn50,
            meanRrMs: mean
        )
    }
}

/// HRV 伪差校正结果：校正后序列 + 掩码 + 校正后时域指标。
public struct HRVArtifactCorrectionResult: Equatable {
    public var rrCorrected: [Double]
    public var artifactMask: [UInt8]
    public var metrics: HRVTimeDomainResult
}

public enum HRVArtifactCorrection {
    /**
     伪差检测 + 插值回填；默认阈值 120ms（口径见 case-06 文档）。
     */
    public static func correct(
        rrMs: [Double],
        thresholdMs: Double = 120.0
    ) throws -> HRVArtifactCorrectionResult {
        if rrMs.isEmpty {
            throw AlgoError.empty
        }
        if rrMs.count < 2 {
            throw AlgoError.tooShort
        }
        if !thresholdMs.isFinite || thresholdMs <= 0 {
            throw AlgoError.invalidArgument
        }

        var corrected = [Double](repeating: 0, count: rrMs.count)
        var mask = [UInt8](repeating: 0, count: rrMs.count)
        let code: Int32 = rrMs.withUnsafeBufferPointer { rBuf in
            corrected.withUnsafeMutableBufferPointer { cBuf in
                mask.withUnsafeMutableBufferPointer { mBuf in
                    guard let rPtr = rBuf.baseAddress,
                          let cPtr = cBuf.baseAddress,
                          let mPtr = mBuf.baseAddress else {
                        return Int32(ALGO_ERR_NULL_POINTER)
                    }
                    return algo_hrv_correct_artifacts(
                        rPtr,
                        rBuf.count,
                        thresholdMs,
                        cPtr,
                        mPtr
                    )
                }
            }
        }
        guard code == ALGO_OK else { throw AlgoError(algoCode: code) }
        let metrics = try HRVTimeDomain.compute(rrMs: corrected)
        return HRVArtifactCorrectionResult(rrCorrected: corrected, artifactMask: mask, metrics: metrics)
    }
}

/// HRV 频域结果 + 中间快照（用于逐环定位漂移）。
public struct HRVFreqDomainResult: Equatable {
    public var lf: Double
    public var hf: Double
    public var lfHfRatio: Double
    public var resampled: [Double]
    public var detrended: [Double]
    public var windowed: [Double]
    public var psd: [Double]
    public var freqs: [Double]
}

public enum HRVFreqDomain {
    /**
     RR(ms) → 4Hz 插值 → 减均值 → Hann → rFFT → LF/HF。

     口径：`docs/02-算法对齐口径/hrv-freq-domain.md`。
     快照与 golden `snapshots` 字段一一对应。
     */
    public static func compute(rrMs: [Double]) throws -> HRVFreqDomainResult {
        if rrMs.isEmpty {
            throw AlgoError.empty
        }

        var lf = 0.0
        var hf = 0.0
        var ratio = 0.0
        var resampled = [Double](repeating: 0, count: Int(ALGO_HRV_FREQ_MAX_TIME))
        var detrended = [Double](repeating: 0, count: Int(ALGO_HRV_FREQ_MAX_TIME))
        var windowed = [Double](repeating: 0, count: Int(ALGO_HRV_FREQ_MAX_TIME))
        var psd = [Double](repeating: 0, count: Int(ALGO_HRV_FREQ_MAX_PSD))
        var freqs = [Double](repeating: 0, count: Int(ALGO_HRV_FREQ_MAX_PSD))
        var nTime = resampled.count
        var nPsd = psd.count

        let code: Int32 = rrMs.withUnsafeBufferPointer { buf in
            guard let base = buf.baseAddress else {
                return Int32(ALGO_ERR_NULL_POINTER)
            }
            return resampled.withUnsafeMutableBufferPointer { rBuf in
                detrended.withUnsafeMutableBufferPointer { dBuf in
                    windowed.withUnsafeMutableBufferPointer { wBuf in
                        psd.withUnsafeMutableBufferPointer { pBuf in
                            freqs.withUnsafeMutableBufferPointer { fBuf in
                                algo_hrv_freq_domain(
                                    base,
                                    buf.count,
                                    &lf,
                                    &hf,
                                    &ratio,
                                    rBuf.baseAddress,
                                    dBuf.baseAddress,
                                    wBuf.baseAddress,
                                    pBuf.baseAddress,
                                    fBuf.baseAddress,
                                    &nTime,
                                    &nPsd
                                )
                            }
                        }
                    }
                }
            }
        }

        guard code == ALGO_OK else { throw AlgoError(algoCode: code) }
        return HRVFreqDomainResult(
            lf: lf,
            hf: hf,
            lfHfRatio: ratio,
            resampled: Array(resampled.prefix(nTime)),
            detrended: Array(detrended.prefix(nTime)),
            windowed: Array(windowed.prefix(nTime)),
            psd: Array(psd.prefix(nPsd)),
            freqs: Array(freqs.prefix(nPsd))
        )
    }
}
