import Foundation
import AlgoC

// MARK: - BLE 分片模拟

/// 模拟 BLE 通知：带序列号的短包（2~3 个 PPG 采样）。
public struct BLEPacket: Equatable {
    public var seq: UInt64
    public var samples: [Double]

    public init(seq: UInt64, samples: [Double]) {
        self.seq = seq
        self.samples = samples
    }
}

/// 缺口策略（对齐口径 streaming-fir.md）。
public enum GapPolicy: Equatable {
    /// 缺失采样填 0，时间轴连续（默认，可与「预插零再整段滤波」对齐）。
    case zeroFill
    /// 不填零，直接接下一个包（时间轴收缩；仅演示，产品需谨慎）。
    case skip
}

// MARK: - RingBuffer

/// 固定容量环形缓冲；溢出时丢最旧样本（流式 lab 用，非生产音频环）。
public struct SampleRingBuffer {
    private var storage: [Double]
    private var head: Int = 0
    private var count_: Int = 0
    public let capacity: Int

    public init(capacity: Int) {
        precondition(capacity > 0)
        self.capacity = capacity
        self.storage = [Double](repeating: 0, count: capacity)
    }

    public var count: Int { count_ }

    public mutating func push(_ values: [Double]) {
        for v in values {
            let idx = (head + count_) % capacity
            if count_ == capacity {
                // 覆盖最旧：头前进
                storage[head] = v
                head = (head + 1) % capacity
            } else {
                storage[idx] = v
                count_ += 1
            }
        }
    }

    /// 弹出最多 `n` 个最旧样本（FIFO）。
    public mutating func popFirst(_ n: Int) -> [Double] {
        let take = min(n, count_)
        var out = [Double]()
        out.reserveCapacity(take)
        for _ in 0..<take {
            out.append(storage[head])
            head = (head + 1) % capacity
            count_ -= 1
        }
        return out
    }
}

// MARK: - Streaming FIR

/// 因果流式 FIR：C 延迟线跨窗连续；与整段逐点因果滤波应对齐。
public final class StreamingFIR {
    private var state = AlgoFIRStreamState()
    private let coeffs: [Double]
    public private(set) var resetCount: Int = 0

    public init(coeffs: [Double] = FIRCoeffs.bandpass) {
        self.coeffs = coeffs
        _ = algo_fir_stream_reset(&state)
    }

    /// 开流或显式演示「错误重置」时调用。
    public func reset() {
        _ = algo_fir_stream_reset(&state)
        resetCount += 1
    }

    public func process(_ x: [Double]) throws -> [Double] {
        if x.isEmpty { throw AlgoError.empty }
        var y = [Double](repeating: 0, count: x.count)
        let code: Int32 = x.withUnsafeBufferPointer { xBuf in
            coeffs.withUnsafeBufferPointer { bBuf in
                y.withUnsafeMutableBufferPointer { yBuf in
                    guard let xp = xBuf.baseAddress,
                          let bp = bBuf.baseAddress,
                          let yp = yBuf.baseAddress else {
                        return Int32(ALGO_ERR_NULL_POINTER)
                    }
                    return algo_fir_stream_process(
                        &state,
                        bp, bBuf.count,
                        xp, xBuf.count,
                        yp, yBuf.count
                    )
                }
            }
        }
        guard code == ALGO_OK else { throw AlgoError(algoCode: code) }
        return y
    }
}

/// 把 BLE 包推入 RingBuffer，按 1 秒窗触发 FIR；处理 seq 缺口。
public final class StreamingFIRPipeline {
    public let windowSize: Int
    public let gapPolicy: GapPolicy
    public let samplesPerMissingPacket: Int
    private var ring: SampleRingBuffer
    private let fir: StreamingFIR
    private var expectedSeq: UInt64?
    /// 是否在每个窗边界错误地 reset（负例演示）。
    public var resetStateEachWindow: Bool

    public private(set) var gapEvents: Int = 0
    public private(set) var outputs: [[Double]] = []

    public init(
        ringCapacity: Int = 50,
        windowSize: Int = 25,
        gapPolicy: GapPolicy = .zeroFill,
        samplesPerMissingPacket: Int = 2,
        resetStateEachWindow: Bool = false,
        coeffs: [Double] = FIRCoeffs.bandpass
    ) {
        self.ring = SampleRingBuffer(capacity: ringCapacity)
        self.windowSize = windowSize
        self.gapPolicy = gapPolicy
        self.samplesPerMissingPacket = samplesPerMissingPacket
        self.resetStateEachWindow = resetStateEachWindow
        self.fir = StreamingFIR(coeffs: coeffs)
    }

    public func ingest(_ packet: BLEPacket) throws {
        if let exp = expectedSeq, packet.seq > exp {
            let missingPackets = Int(packet.seq - exp)
            gapEvents += missingPackets
            if gapPolicy == .zeroFill {
                let fillCount = missingPackets * samplesPerMissingPacket
                if fillCount > 0 {
                    ring.push([Double](repeating: 0, count: fillCount))
                }
            }
        } else if expectedSeq == nil, packet.seq > 0 {
            // 开流即缺口（前缀丢包）
            let missingPackets = Int(packet.seq)
            gapEvents += missingPackets
            if gapPolicy == .zeroFill {
                let fillCount = missingPackets * samplesPerMissingPacket
                if fillCount > 0 {
                    ring.push([Double](repeating: 0, count: fillCount))
                }
            }
        }
        expectedSeq = packet.seq + 1
        ring.push(packet.samples)
        try flushWindows()
    }

    private func flushWindows() throws {
        while ring.count >= windowSize {
            if resetStateEachWindow {
                fir.reset()
            }
            let chunk = ring.popFirst(windowSize)
            let y = try fir.process(chunk)
            outputs.append(y)
        }
    }

    public var flatOutput: [Double] {
        outputs.flatMap { $0 }
    }
}
