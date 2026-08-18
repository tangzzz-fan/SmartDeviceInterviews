// T4-Q3 模拟模型版本双缓冲切换
import Foundation

struct ModelSlot {
    var version: String
    var accuracy: Double
}

final class ModelRouter {
    private(set) var active: ModelSlot
    private var candidate: ModelSlot?

    init(active: ModelSlot) { self.active = active }

    func stage(_ slot: ModelSlot) {
        candidate = slot
        print("暂存候选 \(slot.version) acc=\(slot.accuracy)")
    }

    func promoteIfBetter(minAcc: Double) {
        guard let candidate else {
            print("无候选")
            return
        }
        if candidate.accuracy >= minAcc && candidate.accuracy >= active.accuracy {
            print("切换 \(active.version) → \(candidate.version)")
            active = candidate
            self.candidate = nil
        } else {
            print("拒绝切换，保持 \(active.version)（回滚路径）")
            self.candidate = nil
        }
    }
}

let router = ModelRouter(active: ModelSlot(version: "1.0.0", accuracy: 0.86))
router.stage(ModelSlot(version: "1.1.0", accuracy: 0.84))
router.promoteIfBetter(minAcc: 0.85)
router.stage(ModelSlot(version: "1.2.0", accuracy: 0.88))
router.promoteIfBetter(minAcc: 0.85)
print("当前活跃: \(router.active.version)")
