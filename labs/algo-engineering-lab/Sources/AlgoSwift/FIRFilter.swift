import Foundation
import Accelerate
import AlgoC

/// Case2：FIR 带通。系数来自生成脚本写入的 `ALGO_FIR_BANDPASS_COEFFS`（完整 double）。
public enum FIRCoeffs {
    /// 与 Python `design_bandpass_coeffs()` / golden coeffs.json 同源
    public static var bandpass: [Double] {
        // C 定长数组在 Swift 里会变成巨大 tuple，不能用下标；通过指针按 Double 解读
        withUnsafePointer(to: ALGO_FIR_BANDPASS_COEFFS) { tuplePtr in
            let raw = UnsafeRawPointer(tuplePtr).assumingMemoryBound(to: Double.self)
            return Array(UnsafeBufferPointer(start: raw, count: Int(ALGO_FIR_NUM_TAPS)))
        }
    }
}

public enum FIRFilter {
    /// Naive C 卷积（直接型），对齐 `scipy.signal.convolve(x, b, mode="same")`。
    public static func filterNaive(
        x: [Double],
        coeffs: [Double] = FIRCoeffs.bandpass
    ) throws -> [Double] {
        if x.isEmpty { throw AlgoError.empty }

        var y = [Double](repeating: 0, count: x.count)
        let code: Int32 = x.withUnsafeBufferPointer { xBuf in
            coeffs.withUnsafeBufferPointer { bBuf in
                y.withUnsafeMutableBufferPointer { yBuf in
                    guard let xPtr = xBuf.baseAddress,
                          let bPtr = bBuf.baseAddress,
                          let yPtr = yBuf.baseAddress else {
                        return Int32(ALGO_ERR_NULL_POINTER)
                    }
                    return algo_fir_filter_naive(
                        xPtr, xBuf.count,
                        bPtr, bBuf.count,
                        yPtr, yBuf.count
                    )
                }
            }
        }
        guard code == ALGO_OK else { throw AlgoError(algoCode: code) }
        return y
    }

    /**
     Accelerate 路径：每个输出点用 `vDSP_dotprD` 做乘加，公式与 naive C / scipy same 相同。

     为什么不用整段 `vDSP_convD`：其输入填充与系数方向稍有差池就会整体错位；
     本 lab 优先「与 golden 口径一致」。批量按窗调用（Case5）仍远优于逐 sample 跨边界。
     */
    public static func filterVDSP(
        x: [Double],
        coeffs: [Double] = FIRCoeffs.bandpass
    ) throws -> [Double] {
        if x.isEmpty { throw AlgoError.empty }
        for v in x where !v.isFinite { throw AlgoError.nonFinite }
        for v in coeffs where !v.isFinite { throw AlgoError.nonFinite }
        guard !coeffs.isEmpty else { throw AlgoError.invalidArgument }

        let n = x.count
        let p = coeffs.count
        let start = (p - 1) / 2
        var y = [Double](repeating: 0, count: n)
        var window = [Double](repeating: 0, count: p)

        for i in 0..<n {
            let fullIndex = i + start
            for k in 0..<p {
                window[k] = 0
                if fullIndex >= k {
                    let j = fullIndex - k
                    if j < n {
                        window[k] = x[j]
                    }
                }
            }
            var acc = 0.0
            window.withUnsafeBufferPointer { wBuf in
                coeffs.withUnsafeBufferPointer { bBuf in
                    vDSP_dotprD(
                        wBuf.baseAddress!, 1,
                        bBuf.baseAddress!, 1,
                        &acc,
                        vDSP_Length(p)
                    )
                }
            }
            y[i] = acc
        }
        return y
    }
}
