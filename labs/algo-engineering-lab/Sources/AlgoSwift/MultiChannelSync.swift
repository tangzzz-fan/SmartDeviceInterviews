import Foundation

public struct MultiChannelPacket: Equatable {
    public var seq: Int
    public var channelID: String
    public var sampleCount: Int
    public var t0: Double
    public var dt: Double
    public var samples: [Double]
}

public struct MultiChannelSyncResult: Equatable {
    public var timeline: [Double]
    public var aligned: [String: [Double]]
    public var mask: [String: [Int]]
}

public enum MultiChannelSync {
    /**
     多通道时间轴重建：seq 排序 + round(t/dt_ref) 映射 + zero_fill。
     */
    public static func rebuildTimeline(
        packets: [MultiChannelPacket],
        channels: [String],
        dtRef: Double,
        zeroFill: Bool = true
    ) throws -> MultiChannelSyncResult {
        guard dtRef.isFinite, dtRef > 0 else {
            throw AlgoError.invalidArgument
        }

        var values = [String: [Int: Double]]()
        var present = [String: [Int: Int]]()
        for ch in channels {
            values[ch] = [:]
            present[ch] = [:]
        }

        var maxIdx = -1
        for p in packets.sorted(by: { $0.seq < $1.seq }) {
            guard channels.contains(p.channelID) else { continue }
            for i in 0..<p.samples.count {
                let t = p.t0 + Double(i) * p.dt
                let idx = Int((t / dtRef).rounded())
                guard idx >= 0 else { continue }
                values[p.channelID]?[idx] = p.samples[i]
                present[p.channelID]?[idx] = 1
                if idx > maxIdx { maxIdx = idx }
            }
        }

        if maxIdx < 0 {
            return MultiChannelSyncResult(
                timeline: [],
                aligned: Dictionary(uniqueKeysWithValues: channels.map { ($0, []) }),
                mask: Dictionary(uniqueKeysWithValues: channels.map { ($0, []) })
            )
        }

        let timeline = (0...maxIdx).map { Double($0) * dtRef }
        var aligned = [String: [Double]]()
        var mask = [String: [Int]]()
        for ch in channels {
            var arr = [Double]()
            var m = [Int]()
            arr.reserveCapacity(maxIdx + 1)
            m.reserveCapacity(maxIdx + 1)
            for i in 0...maxIdx {
                if let v = values[ch]?[i] {
                    arr.append(v)
                    m.append(1)
                } else {
                    arr.append(zeroFill ? 0.0 : .nan)
                    m.append(0)
                }
            }
            aligned[ch] = arr
            mask[ch] = m
        }
        return MultiChannelSyncResult(timeline: timeline, aligned: aligned, mask: mask)
    }
}
